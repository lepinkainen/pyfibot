##
## ODB2 - Pure Python object database
## Copyright (C) 2004 Sami Hangaslammi (shang@jyu.fi)
##
"""
File Storage Utilities
"""

from __future__ import generators

from types import SliceType
from os.path import getsize as _filesize, exists
from bisect import bisect
import math
from sys import maxint
import cPickle
import struct
import time

_BLOCKSIZE = 64*1024
_MAXSIZE = maxint

class allocerror(Exception): pass

def _fmtr(addr,size):
    end = addr+size
    #return "0x%X-0x%X" % (addr,end)
    return "%i-%i" % (addr,end)


## ----- Allocation Table ----- ##

class AllocTab(object):
    """
    AllocTab is used for keeping track which segments of a value
    area are "in use" and which are "free".
    """
    
    def __init__(self):
        self._allocated = []
        self._free = []

    def allocate(self, addr, size):
        """allocate(addr, size) -> None

        Mark 'size' values starting from 'addr' as used. The marked
        values must be free and the allocation should extend a continuous
        "used" segment if possible. Use the find_free method to find
        a valid location for the allocation.
        """
        if size == 0:
            return
        if addr < 0:
            raise allocerror, "invalid allocation address %i" % addr
        if size < 0:
            raise allocerror, "invalid allocation size %i" % size
        free = self._free
        allocated = self._allocated
        
        if not free: # special case: no free space
            if not allocated: # special case: no space or allocations
                if addr != 0:
                    raise allocerror, "invalid allocation %s, must begin allocation at 0x%X" % (_fmtr(size,addr),0)
                allocated.append((addr,size))
                return
            if len(allocated) != 1:
                raise allocerror, "allocation table corrupted, %s allocations and no free segments" % len(allocated)
            elif allocated[0][0] != 0: # sanity check
                raise allocerror, "allocation table corrupted, only allocation is %s" % _fmtr(*allocated[0])
            a,s = allocated[0]
            if addr != a+s: # sanity check
                raise allocerror, "invalid allocation %s, does not append to %s" % (_fmtr(addr,size), _fmtr(a,s))
            allocated[0] = (a,s+size)
            return
        
        endfree = not allocated or free[-1][0] > allocated[-1][0]
        if endfree:
            endaddr = free[-1][0]+free[-1][1]
        else:
            endaddr = allocated[-1][0]+allocated[-1][1]
            
        if addr > endaddr: # sanity check
            raise allocerror, "invalid allocation %s, last address is at 0x%X" % (_fmtr(addr,size), endaddr)
                
        if addr == endaddr: # special case: append
            if endfree: # sanity check
                raise allocerror, "invalid allocation %s, last free = %s" % (_fmtr(addr,size), _fmtr(*free[-1]))
            # enlarge last segment
            a,s = allocated[-1] 
            allocated[-1] = (a,s+size)
            return

        # retrieve the segment of free space
        fi = self._freei(addr)
        if fi < 0: # sanity check
            raise allocerror, "invalid allocation %s, first free = %s" % (_fmtr(addr,size), _fmtr(*free[0]))
        fa,fs = free[fi]

        previ = self._alloci(addr)
        nexti = previ+1
        
        if addr != fa: # sanity check
            raise allocerror, "invalid allocation %s, free = %s" % (_fmtr(addr,size), _fmtr(fa,fs))

        if previ >= 0: # special case: there is a previous segment
            # merge with previous
            pa,ps = allocated[previ]
            if pa+ps != addr: # sanity check
                raise allocerror, "allocation table corrupted 0x%X does not follow %s" % (addr, _fmtr(pa,ps))
            allocated[previ] = (pa,ps+size)
            i = previ
        else:
            if addr != 0: # sanity check
                raise allocerror, "first allocation can't be 0x%X" % _fmtr(addr,size)
            allocated.insert(0, (addr,size))
            i = 0
            nexti = 1

        ## TODO: optimize (common case first)
        if size > fs: # special case: size exceeds free segment size
            if fi != len(free)-1: # sanity check
                raise allocerror, "invalid allocation %s, free = %s" % (_fmtr(addr,size), _fmtr(fa,fs))
            # enlarge last free segment and fill it
            del free[-1]
        elif size == fs: # special case: free segment is filled exactly
            if nexti == len(allocated): # special case: no following segment
                if fi != len(free)-1: # sanity check
                    raise allocerror, "allocation table corrupted, no segments after free %s" % _fmtr(fa,fs)
            else:
                # combine with following segment
                na,ns = allocated[nexti]
                if addr+size != na: # sanity check
                    raise allocerror, "alloccation table corrupted, segments %s and %s apart" % (_fmtr(fa,fs),_fmtr(na,ns))
                a,s = allocated[i]
                allocated[i] = (a, ns+s)
                del allocated[nexti]
            del free[fi]
        else: # free segment is party filled
            free[fi] = (fa+size,fs-size)

    def free(self, addr, size):
        """free(addr, size) -> None
        
        Mark an allocated segment as "free".
        """
        if size == 0:
            return
        if addr < 0:
            raise allocerror, "invalid deallocation address %i" % addr
        if size < 0:
            raise allocerror, "invalid deallocation size %i" % size
        free = self._free
        allocated = self._allocated

        if not allocated: # sanity check
            raise allocerror, "nothing to deallocate"

        if not self.is_allocated(addr,size):
            raise allocerror, "%s is not allocated" % (_fmtr(addr,size))

        ai = self._alloci(addr)
        if ai < 0: # sanity check
            raise allocerror, "invalid deallocation %s, first allocation = %s" % (_fmtr(addr,size), _fmtr(*allocated[0]))
        aa,as = allocated[ai]
        if addr+size > aa+as: # sanity check
            raise allocerror, "invalid deallocation %s, alloc = %s" % (_fmtr(addr,size), _fmtr(aa,as))

        previ = self._freei(addr)
        nexti = previ+1


        if addr == aa: # special case: from beginning of allocation
            if previ >= 0: # there is a previous free segment
                pa,ps = free[previ]
                free[previ] = (pa,ps+size)
                i = previ
            else:
                free.insert(0, (addr,size))
                i = 0
                nexti = 1
            if size == as: # special case: free the whole segment
                if nexti < len(free):
                    a,s = free[i]
                    na,ns = free[nexti]
                    free[i] = (a,s+ns)
                    del free[nexti]
                del allocated[ai]
            else:
                allocated[ai] = (aa+size,as-size)
        else: # from middle of allocation
            allocated[ai] = (aa,addr-aa)            
            if addr+size == aa+as: # special case: free till the end of segment
                if nexti < len(free): # if there is a next free segment
                    na,ns = free[nexti]
                    free[nexti] = (addr, size+ns)
            else:
                free.insert(nexti, (addr,size))
                allocated.insert(ai+1, (addr+size,aa+as-addr-size))

    def check_integrity(self):
        """check_integrity() -> boolean

        Check that the allocation table hasn't been corrupted.
        (For debugging purposes)
        """
        all = self._free + self._allocated
        if not all:
            return 1
        free = self._free
        allocated = self._allocated
        all.sort()
        if all[0][0] != 0:
            return 0
        last = all[0]
        for x in all[1:]:
            if x[0] != last[0]+last[1]:
                return 0
            if (x in free and last in free) or (x in allocated and last in allocated):
                return 0
            last = x
        return 1

    def find_free(self, size):
        """find_free(size) -> (addr,size)

        Find a free segment of at least 'size' and return its
        address. This method does not mark the segment as "used",
        you have to do that separately with the allocate method.
        """
        free = self._free
        allocated = self._allocated
        if not free:
            if not allocated:
                return (0,size)
            return (allocated[-1][0]+allocated[-1][1],size)

        ## TODO: keep a list of free segments sorted by size and bisect instead of loop
        for a,s in free:
            if s >= size:
                return a,s

        endfree = not allocated or free[-1][0] > allocated[-1][0]
        if endfree:
            return (free[-1][0],size)
        else:
            endaddr = allocated[-1][0]+allocated[-1][1]
            return (endaddr,size)

    def alloc_greedy(self, size, maxsize=1.3):
        """alloc_greedy(size, maxsize=1.3) -> (addr,size)

        Similar to alloc_free, this method finds a suitable location
        and marks at least 'size' bytes as "used". However, if the
        total size of the continuous free segment is less than
        size * maxsize, the whole segment is allocated to prevent
        defragmentation.
        """
        a,s = self.find_free(size)
        if float(s)/size < maxsize:
            self.allocate(a,s)
            return (a,s)
        self.allocate(a,size)
        return (a,size)

    def alloc_free(self, size):
        """alloc_free(size) -> addr

        Marks exactly 'size' values as "used" and returns the address
        of the first value.
        """
        free = self.find_free(size)
        self.allocate(free[0],size)
        return free[0]

    def total_allocated(self):
        """total_allocated() -> int

        The total number of values marked as "used".
        """
        return reduce(lambda x,y: x+y[1], self._allocated, 0)
        
    def total_free(self):
        """total_free() -> int

        The total number of values marked as "free".
        """
        return reduce(lambda x,y: x+y[1], self._free, 0)

    def fragments(self):
        """fragments() -> int

        Return a number of continuous used/free areas
        in the allocation table.
        """
        return len(self._allocated) + len(self._free)

    def is_allocated(self, addr, size):
        """is_allocated(addr, size) -> boolean

        Check if all values in the given range are marked as "used".
        """
        allocated = self._allocated
        if not allocated:
            return 0
        i = self._alloci(addr)
        if i < 0:
            return 0
        a,s = allocated[i]
        if addr+size <= a+s:
            return 1
        return 0

    def is_free(self, addr, size):
        """is_free(addr, size) -> boolean

        Check if all values in the given range are marked as "free".
        """
        free = self._free
        if not free:
            return 0
        i = self._freei(addr)
        if i < 0:
            return 0
        a,s = free[i]
        if addr+size <= a+s:
            return 1
        return 0

    def __str__(self):
        free = self._free
        allocated = self._allocated
        l = free + allocated
        l.sort()
        result = []
        app = result.append
        for x in l:
            a,s = x
            if x in free:
                app("Free  ")
            else:
                app("Alloc ")
            app(_fmtr(a,s))
            app("  (%i bytes)" % s)
            app("\n")
        return "".join(result)

    def _freei(self, addr):
        return bisect(self._free, (addr, _MAXSIZE))-1

    def _alloci(self, addr):
        return bisect(self._allocated, (addr, _MAXSIZE))-1

    def _allocate(self, addr, size):
        old = self._free[:], self._allocated[:]
        self.allocate_(addr,size)
        if not self.check_integrity():
            print "ALLOCATION TABLE CORRUPTED"
            print "allocated %s" % _fmtr(addr,size)
            print "\nCurrent:"
            print str(self)
            self._free, self._allocated = old
            print "Old:"
            print str(self)
            raise allocerror, "integrity compromised"

    def _free(self, addr, size):
        old = self._free[:], self._allocated[:]
        self.free_(addr,size)
        if not self.check_integrity():
            print "ALLOCATION TABLE CORRUPTED"
            print "freed %s" % _fmtr(addr,size)
            print "\nCurrent:"
            print str(self)
            self._free, self._allocated = old
            print "Old:"
            print str(self)
            raise allocerror, "integrity compromised"
    

## ----- Random Access File ----- ##

class RAF(object):
    """Random Access File

    A utility class for reading and writing binary data
    to a file in random access mode.
    """
    
    def __init__(self, filename):
        """RAF(filename) -> RAF object

        Open a file in random access mode. If the file doesn't
        exist it is created.
        """
        fn = self.filename = filename
        f = file(fn, "ab")
        f.close()
        self.len = _filesize(self.filename)
        self.file = None

    def flush(self):
        """flush() -> None

        Flush the contents of the write buffer. Relies on the
        underlying file.flush implementation.
        """
        if self.file is None:
            return
        self.file.flush()

    def close(self):
        """close() -> None

        Close the file. Additional operations to the RAF
        object will re-open the file.
        """
        if self.file is None:
            return
        self.file.close()
        self.file = None

    def put(self, addr, data, size=None):
        """put(addr, data) -> None

        Write upto 'size' bytes from a string into the RAF at position
        'addr'. The size of the file is increased as needed. If 'data' is
        a file-like object (has a method called "read"), up to 'size' bytes
        are read from it and written to the RAF.
        """
        f = self._file()
        f.seek(addr)
        if not data:
            return
        if hasattr(data, "read"):
            if size is not None:
                left = size
            else:
                left = _BLOCKSIZE
            while 1:
                s = data.read(min(_BLOCKSIZE, left))
                if not s:
                    return
                if size is not None:
                    left -= len(s)
                if left <= 0:
                    return
                f.write(s)
        if size is None:
            f.write(data)
        else:
            f.write(data[:size])

    def get(self, addr, size):
        """get(addr, size) -> string

        Read upto 'size' bytes from the RAF at position 'addr'.
        """
        f = self._file()
        f.seek(addr)
        if size:
            return f.read(size)
        return ""

    def append(self, data):
        """append(data) -> None

        Append a string to the end of the RAF
        """
        f = self._file()
        f.seek(0,2)
        f.write(data)

    def fill(self, addr, repeats, data):
        """fill(addr, repeats, data) -> None

        Fill a segment starting from 'addr' by repeating
        the contents of data.
        """
        if not repeats:
            return
        mul = max(int(float(_BLOCKSIZE) / len(data)+0.5),1)
        mul = min(mul, repeats)
        f = self._file()
        f.seek(addr)
        left = repeats
        block = data * mul
        while 1:
            f.write(block)
            left -= mul
            if not left:
                return
            if left < mul:
                f.write(data * left)
                return

    def copy(self, fromaddr, toaddr, size):
        """copy(fromaddr, toaddr, size) -> None

        Copy data from one position to another.
        """
        if size <= _BLOCKSIZE:
            self.put(toaddr, self.get(fromaddr, size))
            return
        written = 0
        left = size
        while 1:
            tmp = self.get(fromaddr + written, min(left, _BLOCKSIZE))
            self.put(toaddr + written, tmp)
            written += len(tmp)
            left -= len(tmp)
            if not left:
                return

    def swap(self, fromaddr, toaddr, size):
        """swap(fromaddr, toaddr, size) -> None

        Swap the data stored in two position.
        """
        if size <= _BLOCKSIZE:
            tmp = self.get(fromaddr, size)
            self.copy(toaddr, fromaddr, size)
            self.put(toaddr, tmp)
            return
        written = 0
        left = size
        while 1:
            bsize = min(left, _BLOCKSIZE)
            tmp = self.get(fromaddr+written, bsize)
            self.copy(toaddr+written, fromaddr+written, len(tmp))
            self.put(toaddr, tmp)
            written += len(tmp)
            left -= len(tmp)
            if not left:
                return

    def _open(self):
        self.file = file(self.filename, "r+b")

    def _file(self):
        if self.file is None:
            self._open()
        return self.file

    def _checksize(self):
        f = self._file()
        f.seek(0,2)
        self.len = f.tell()
        return self.len


class FileHeader(object):
    """Generic header object for storing indexing etc. information"""



## ----- File Memory ----- ##

class FileMem(object):
    """File Memory

    A random access file from which you can allocate chunks
    using C-like malloc, realloc and free.
    """
    
    _ptr = "!2Q"
    _allocblock = 16
    pickle_proto = -1
    
    def __init__(self, filename, allocblock = None):
        if allocblock is not None:
            self._allocblock = allocblock
        self.filename = filename        
        self.header = None
        if not exists(filename):
            self._new()
        else:
            self.file = RAF(self.filename)
            self._load_header()

    def flush(self):
        """flush() -> None

        Flush the contents of the write buffer. Relies on the
        underlying file.flush implementation.
        """
        self._save_header()
        self.file.flush()

    def close(self):
        """close() -> None

        Closes the file.
        """
        self._save_header()
        self.file.close()

    def alloc(self, size):
        """alloc(size) -> (address, size)

        Allocates an area of the file that has at least 'size' bytes.
        The actual allocated size will be returned and should be kept
        for deallocation purposes.
        """
        block = self._allocblock
        realsize = int(math.ceil(size / float(block)))*block
        return self.header.alloctab.alloc_greedy(realsize)

    def free(self, addr, size):
        """free(address, size) -> None

        Free a previously allocated area of the file.
        """
        self.header.alloctab.free(addr,size)

    def realloc(self, addr, size, new_size):
        """realloc(address, size, newsize) -> (address, size)

        Copy the contents of an address area to a new address and
        reserve more bytes after the data.
        """
        self.free(addr,size)
        a,s = self.alloc(new_size)
        if a != addr:
            self.file.copy(addr, a, size)
        return a,s

    def _new(self):
        self.file = RAF(self.filename)
        self.header = FileHeader()
        a = self.header.alloctab = AllocTab()
        sz = struct.calcsize(self._ptr)
        a.allocate(0, sz)
        self._hdrptr = None

    def _get_hdrptr(self):
        ptrs = self.file.get(0, struct.calcsize(self._ptr))
        a,s = struct.unpack(self._ptr, ptrs)
        self._hdrptr = a,s
        return a,s

    def _put_hdrptr(self):
        self.file.put(0, struct.pack(self._ptr, *self._hdrptr))

    def _load_header(self):
        a,s = self._get_hdrptr()
        f = self.file
        f.get(a,0)
        self.header = cPickle.load(f._file())

    def _save_header(self):
        f = self.file
        tabs = cPickle.dumps(self.header, self.pickle_proto)
        if self._hdrptr:
            a,s = self._hdrptr
            if len(tabs) > s:                
                self.free(a,s)
                s = int(len(tabs)*1.5)
                a,s = self.alloc(s)
        else:
            s = int(len(tabs)*1.5)
            a,s = self.alloc(s)
        tabs = cPickle.dumps(self.header, self.pickle_proto)
        assert len(tabs) <= s
        f.put(a,tabs)
        self._hdrptr = (a,s)
        self._put_hdrptr()



## ----- ID Table ----- ##

class IDTable(object):
    """ID Table

    Tracks ID numbers in a scalable way (O(1) access via id)
    """
    _ptrtype = FileMem._ptr
    _ptrsz = struct.calcsize(_ptrtype)
    _initsize = 100
    
    def __init__(self, raf):
        self._alloc = AllocTab()
        self._raf = raf
        self._new()

    def _new(self):
        cap = self._capacity = self._initsize
        sz = struct.calcsize(self._ptrtype) * cap
        self._ptr = self._raf.alloc(sz)

    def __getstate__(self):
        state = {}
        state.update(self.__dict__)
        del state['_raf']
        return state

    def _grow(self):
        cap = self._capacity
        sz = self._ptrsz * cap
        new_cap = int(cap * 1.5)
        new_sz = self._ptrsz * new_cap
        sz *= cap
        addr,size = self._ptr
        self._ptr = self._raf.realloc(addr, size, new_sz)
        self._capacity = new_cap

    def new_id(self):
        a = self._alloc.alloc_free(1)
        if a >= self._capacity:
            self._grow()
        self[a] = (0,0)
        return a

    def __getitem__(self, id):
        if not isinstance(id, int):
            raise TypeError, "id must be an integer"
        sz = self._ptrsz
        if id >= self._capacity or id < 0 or id not in self:
            raise ValueError, "invalid id: %s" % id
        addr = self._ptr[0] + id * sz
        data = self._raf.file.get(addr, sz)
        ptr = struct.unpack(self._ptrtype, data)
        return ptr

    def __setitem__(self, id, ptr):
        if not isinstance(id, int):
            raise TypeError, "id must be an integer"
        if id >= self._capacity or id < 0 or id not in self:
            raise ValueError, "invalid id: %s" % id
        data = struct.pack(self._ptrtype, *ptr)
        addr = self._ptr[0] + id * self._ptrsz
        self._raf.file.put(addr, data)

    def __contains__(self, id):
        if not isinstance(id, int):
            raise TypeError, "id must be an integer"
        return self._alloc.is_allocated(id, 1)

    def __delitem__(self, id):
        if not isinstance(id, int):
            raise TypeError, "id must be an integer"
        if id not in self:
            raise ValueError, "invalid id %s" % id
        self[id] = (0,0)
        self._alloc.free(id, 1)

    def __len__(self):
        return self._alloc.total_allocated()

    def iterids(self):
        for a,s in self._alloc._allocated:
            for x in xrange(s):
                yield a+x
        

## ----- Object Storage ----- ##

class ObjectStorage(FileMem):
    """Object Storage

    File storage for saving Python objects (using pickle) and referencing
    them by an id number. The Object Storage can be used like a dictionary,
    except that new ids must be reserved using new or new_id before assignment.

    The ObjectStorage is still pretty low level, and is meant to be used as
    the base implementation for more advanced persistence systems.

    Example:
    
    >>> storage = ObjectStorage("mystorage")
    >>> obj = [1,2,3]
    >>> id = storage.new(obj)
    >>> print storage[id]
    [1,2,3]
    >>> del storage[id]
    >>> print id in storage
    False

    or using new_id()...

    >>> storage = ObjectStorage("mystorage")
    >>> obj = [1,2,3]
    >>> id = storage.new_id()
    >>> storage[id] = obj
    """
    pickle_proto = -1

    def has_id(self, id):
        return id in self.header.idtab

    def iterids(self):
        return self.header.idtab.iterids()

    def new_id(self):
        return self.header.idtab.new_id()

    def new(self, obj):
        """new(obj) -> id
        
        Puts an object into the db and creates a new id for it"""
        data = cPickle.dumps(obj, self.pickle_proto)
        idtab = self.header.idtab
        id = idtab.new_id()
        s = len(data)
        a,s = self.alloc(s)
        self.file.put(a,data)
        idtab[id] = (a,s)
        return id

    def get_pickle(self, id):
        idtab = self.header.idtab
        a,s = idtab[id]
        if (a,s) == (0,0):
            raise ValueError, "unallocated id %i" % id
        data = self.file.get(a,s)
        return data

    def set_pickle(self, id, data):
        idtab = self.header.idtab
        a,s = idtab[id]
        if len(data) > s:
            new_s = int(len(data)*1.5)
            self.free(a,s)
            a,s = self.alloc(new_s)
            idtab[id] = (a,s)
        elif len(data) < s*0.2: # if the pickle is considerably smaller, save space
            new_s = int(len(data)*1.5)
            self.free(a,s)
            a,s = self.alloc(new_s)
            idtab[id] = (a,s)
        self.file.put(a, data)

    def __setitem__(self, id, obj):
        data = cPickle.dumps(obj, self.pickle_proto)
        self.set_pickle(id, data)

    def __getitem__(self, id):
        data = self.get_pickle(id)
        return cPickle.loads(data)

    def __delitem__(self, id):
        idtab = self.header.idtab
        a,s = idtab[id]
        self.free(a,s)
        del idtab[id]

    def __contains__(self, id):
        return self.has_id(id)

    def __len__(self):
        """number of objects"""
        return len(self.header.idtab)

    
    def _new(self):
        FileMem._new(self)
        self.header.idtab = IDTable(self)

    def _load_header(self):
        FileMem._load_header(self)
        self.header.idtab._raf = self



class _Tier(dict):
    def __init__(self):
        self._next = None  ## id of next dictionary or None
        self._last_access = {}

    def __setitem__(self, key, value):
        dict.__setitem__(key, value)
        self._last_access[key] = time.time()

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        self._last_access[key] = time.time()
        return value

    def __contains__(self, key):
        c = dict.__contains__(self, key)
        if c:
            self._last_access[key] = time.time()

    has_key = __contains__

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        del self._last_access[key]

    def update(self, src):
        for k,v in src:
            self[k] = v

    def clear(self):
        dict.clear(self)
        self._last_access.clear()


## ----- Tiered Dictionary ----- ##

class TierDict(object):
    """Tiered Dictionary (WORK IN PROGRESS)

    Persistent dictionary that is divided into constant sized "tiers" and
    only maximum of two tiers are kept in memory at once. If keys are not
    accessed, they gradually drop into lower tiers.
    """
    
    def __init__(self, objstor, limit=1000):
        self._storage = objstor
        self._first = _Tier()
        self._limit = limit

    def __setitem__(self, key, value):
        self._first[key] = value
        ## TODO: check first size

    def __getitem__(self, key):
        tier = self._first
        while key not in tier:
            if tier._next is None:
                raise KeyError, key
            id = tier._next
            tier = self._storage[id]
        value = tier[key]
        if tier is not self._first: ## move to first tier
            del tier[key]
            self._storage[id] = tier
            self._first[key] = value
            ## check size of first
        return value
                

    def __delitem__(self, key):
        id = None
        tier = self._first
        while 1:
            if key in tier:
                del tier[key]
                if id is not None:
                    self._storage[id] = tier
            id = tier._next
            if id is None:
                return
            tier = self._storage[id]
            

    def update(self, src):
        for key in src:
            self[key] = src[key]

    def clear(self):
        id = self._first._next
        self._first.clear()
        while id is not None:
            next = self._storage[id]._next
            del self._storage[id]
            id = next

    def __contains__(self, key):
        tier = self._first
        while key not in tier:
            id = tier._next
            if id is None:
                return False
            tier = self._storage[id]
        if tier is not self._first: ## move to first tier
            del tier[key]
            self._storage[id] = tier
            self._first[key] = value
            ## check size of first
        return True

    has_key = __contains__

    def iterkeys(self):
        pass

    def itervalues(self):
        pass

    def iteritems(self):
        pass

    def keys(self):
        pass

    def items(self):
        pass

    def values(self):
        pass


class Shelve(object):
    """Shelve

    A pure Python shelve implementation that uses the Object Storage.
    Still has the same limitation as dumbdb, that all keys are loaded
    into memory when the shelve is opened, but otherwise it works much
    faster and is more reliable.
    """
   
    def __init__(self, filename):
        self._storage = ObjectStorage(filename)
        if len(self._storage) == 0:
            self._new()
        else:
            self._load_keys()

    def _new(self):
        self._keys = {}
        id = self._storage.new(self._keys)
        assert id == 0
        self._storage.flush()

    def _load_keys(self):
        self._keys = self._storage[0]
        
    def _save_keys(self):
        self._storage[0] = self._keys

    def flush(self):
        self._save_keys()
        self._storage.flush()

    def close(self):
        self.flush()
        self._storage.close()
        self._storage = None

    def open(self, filename):
        if self._storage is not None:
            self.close()
        self.__init__(filename)

    def __setitem__(self, key, value):
        keys = self._keys
        if key not in keys:
            id = self._storage.new(value)
            keys[key] = id
            return
        id = keys[key]
        self._storage[id] = value

    def __getitem__(self, key):
        id = self._keys[key]
        return self._storage[id]

    def __delitem__(self, key):
        id = self._keys[key]
        del self._storage[id]

    def __iter__(self):
        return self.iterkeys()

    def __contains__(self, key):
        return key in self._keys

    def has_key(self, key):
        return self._keys.has_key(key)

    def keys(self):
        return self._keys.keys()

    def values(self):
        return [self._storage[id] for id in self._keys.values()]

    def items(self):
        return zip(self.keys(), self.values())

    def iterkeys(self):
        return self._keys.iterkeys()

    def itervalues(self):
        for id in self._keys.itervalues():
            yield self._storage[id]

    def iteritems(self):
        for key,id in self._keys.iteritems():
            yield (key, self._storage[id])

