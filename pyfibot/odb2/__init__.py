##
## ODB2 - Pure Python object database
## Copyright (C) 2004 Sami Hangaslammi (shang@jyu.fi)
##

import weakref
import gc
import time
import copy
import cPickle

import filestr

class ODBError(Exception): pass
class NotInitialised(ODBError): pass
class AlreadyInitialised(ODBError): pass
class NoSuchRoot(ODBError): pass
class InvalidObject(ODBError): pass
class RestoreError(ODBError): pass
class NoTransaction(ODBError): pass
error = ODBError ## so you can catch odb.error

from trdict import TrackingDict

## --- option flags ---
_auto_wake = True
_auto_transaction = False
_use_data_cache = True
_use_object_cache = False

_storage = None
_storage_cache = TrackingDict()
_object_cache = TrackingDict()
_roots = {}

_transaction = None ## current transaction
_transactions = weakref.WeakKeyDictionary()
_pickle_proto = -1

_debug_info = 0

_allocblock = 256

def open(filename, pickle_proto=None):
    global _storage, _roots, _pickle_proto
    if pickle_proto is not None:
        _pickle_proto = pickle_proto
    if _storage is not None:
        raise AlreadyInitialised
    _storage = filestr.ObjectStorage(filename, _allocblock)
    _storage.pickle_proto = _pickle_proto
    if not _storage.has_id(0):
        _roots = {}
        id = _storage.new(_roots)
        assert id == 0
    else:
        _roots = _storage[0]

def set_debug(flag):
    global _debug_info
    _debug_info = flag

def set_auto_wake(flag):
    global _auto_wake
    _auto_wake = flag

def set_auto_transaction(flag):
    global _auto_transaction
    _auto_transaction = flag

def set_data_cache(flag):
    global _use_data_cache
    _use_data_cache = flag

def set_object_cache(flag):
    global _use_object_cache
    _use_object_cache = flag

def set_flags(debug=None, auto_wake=None, auto_transaction=None, data_cache=None, object_cache=None):
    if debug is not None: set_debug(debug)
    if auto_wake is not None: set_auto_wake(auto_wake)
    if auto_transaction is not None: set_auto_transaction(auto_transaction)
    if data_cache is not None: set_data_cache(data_cache)
    if object_cache is not None: set_object_cache(object_cache)

def transaction():
    return _transaction

def new_transaction():
    global _transaction
    t = _transaction = ODBTransaction()
    return t

def clear_transaction():
    global _transaction
    _transaction = None

def clear_cache(timelimit=0):
    if _use_data_cache:
        _storage_cache.del_old(timelimit)
    if _use_object_cache:
        _object_cache.del_old(timelimit)

def close():
    global _storage, _roots
    if _storage is None:
        raise NotInitialised
    _roots = {}
    _storage.close()
    _storage = None

class TransactionError(ODBError): pass
class CommitConflict(TransactionError): pass

class ODBTransaction(object):

    def __new__(cls):
        o = object.__new__(cls)
        _transactions[o] = None
        if _debug_info:
            print "new transaction %s" % o
        return o

    def __init__(self):
        self._cache = {} ## id -> proxy/object
        self._commiting = False
        self._count = 0
        self._aborted = False
        self._new_roots = {}
        self._read_roots = {}

        self._write_buffer = {}

        ## actions made by other transactions during this transaction
        self._other_reads = {}
        self._other_writes = {}
        self._other_roots = {}

    def __getattribute__(self, key):
        ## EXPERIMENTAL: for automatically setting self as the current transaction when methods are accessed        
        global _transaction
        _transaction = self
        return object.__getattribute__(self, key)

    def activate(self):
        """transaction.activate() -> None

        Activate this transaction.
        """
        global _transaction
        if self._aborted:
            raise TransactionError, "Cannot activate a finished transaction"
        if self._commiting:
            raise TransactionError, "Cannot activate a transaction that is commiting data"
        _transaction = self

    def commit(self):
        """transaction.commit() -> int

        Returns the number of objects updated in the commit. The method will
        throw CommitConflict if another transaction has modified the same
        objects.
        """
        global _transaction
        if self._aborted:
            raise TransactionError, "Cannot commit a finished transaction"
        if self._commiting:
            raise TransactionError, "Already commiting this transaction"
        if _storage is None:
            raise NotInitialised

        if _debug_info:
            print "committing transaction %s" % self

        try:
            self._commiting = True
            _transaction = self

            deletions = {}
            reads = {}
            writes = {}

            ## Check for conflicts
            for k,v in self._cache.items():
                if not isinstance(v, ODBProxy) and k in self._other_writes:
                    raise CommitConflict
            for k,v in self._new_roots.items():
                if k in self._other_roots:
                    raise CommitConflict
            for k in self._read_roots:
                if k in self._other_roots:
                    raise CommitConflict

            ## Write updated objects and mark read objects
            for k,v in self._cache.items():
                if not isinstance(v, ODBProxy):
                    id = v._p_id
                    if v._p_deleted:
                        writes[id] = None
                        deletions[id] = None
                    elif v._p_changed:
                        writes[id] = None
                        self._store_object(v)
                    else:
                        reads[id] = None

            new_roots = {}
            ## Validate new roots
            for k,v in self._new_roots.iteritems():
                id = self._flatten_object(v)
                new_roots[k] = id

        except:
            self._commiting = False
            raise

        ## Everything has been pickled succesfully. Now do the real thing.

        ## Update the status of other transactions
        for t in _transactions:
            if t is not self:
                t._other_reads.update(reads)
                t._other_writes.update(writes)
                t._other_roots.update(new_roots)

        ## Remove deleted items
        for id in deletions:
            if id in _storage:
                del _storage[id]
                self._count += 1
            if _use_data_cache and id in _storage_cache: ## TODO: faster to try-catch
                del _storage_cache[id]
            if _use_object_cache and id in _object_cache:
                del _object_cache[id]

        ## Write updated objects
        for id, pckl in self._write_buffer.iteritems():
            if id in _storage:
                if _debug_info:
                    print "writing object %i to file" % id
                _storage.set_pickle(id, pckl)
                if _use_data_cache: _storage_cache[id] = pckl
                self._count += 1
            self._flatten_object(self._cache[id])

        ## Write new roots
        if new_roots:
            _roots.update(new_roots)
            _storage[0] = _roots
            

        _storage.flush()

        count = self._count
        self._aborted = True
        self._commiting = False
        del _transactions[self]
        if _transaction is self:
            _transaction = None
        return count
                    

    def restart(self):
        """transaction.restart() -> None

        Cancel all changes and restart the transaction. All objects waken
        by this transaction are put back to hibernation and must be reawakened.
        """
        if self._aborted:
            raise TransactionError, "Cannot restart a finished transaction"
        self.__init__() ## TODO

    def abort(self):
        """transaction.abort() -> None

        Cancel all changes and invalidate this transaction.
        """
        global _transaction
        self.__init__() ## TODO
        del _transactions[self]
        self._aborted = True
        if _transaction is self:
            _transaction = None
        
    ### --- ###

    def get_roots(self):
        """transaction.get_roots() -> [list of root keys]"""
        return _roots.keys() ## TODO

    def get_root(self, name=""):
        """transaction.get_root([name]) -> root

        Return a root object of the database and awaken it.
        """
        if name in self._new_roots:
            return self._new_roots[name]
        else:
            if name not in _roots:
                raise NoSuchRoot, name
            id = _roots[name]
        self._read_roots[name] = None
        if name in self._other_roots:
            del self._other_roots[name]
        proxy = self._restore_object(id)
        return self.wake(proxy)
        

    def set_root(self, name, obj=None):
        """transaction.set_root([name,] object) -> None

        Assign a root object for the database. Effective after commit.
        """
        if obj is None:
            obj = name
            name = ""
        self.wake(obj)
        if not isinstance(obj, (ODBObject, ODBProxy)):
            raise TypeError, "root objects must be instances of ODBObject"
        if _storage is None:
            raise NotInitialised
        self._new_roots[name] = obj

    def mark_changed(self, obj):
        """transaction.mark_changed(object) -> None

        Mark an object as "changed" so that it will be written to the
        database when committing the transaction. Usually ODBObjects can
        keep track of this automatically, but this method might be needed
        if an object has non-odb-aware mutable attributes.
        """
        global _transaction
        _transaction = self
        obj.__odb_changed__()

    def wake(self, *objs):
        """transaction.wake(object[,object2][,object3]...) -> object

        Awaken a proxy object so that it can be used in operations.
        """
        global _transaction
        _transaction = self
        for obj in objs:
            if not isinstance(obj, ODBProxy):
                continue
            self._restore_proxy(obj)
        if len(objs) == 1:
            return objs[0]
        return objs

    def delete(self, obj):
        """transaction.delete(object) -> None
        Cause an object to be deleted from database when this
        transaction is committed.
        """        
        global _transaction
        _transaction = self
        if not isinstance(obj, (ODBProxy, ODBObject)):
            raise TypeError, "cannot remove a non-odb object"
        self.wake(obj)
        if obj._p_deleted:
            return
        obj.__odb_changed__()
        obj._p_deleted = True

    def _reduce_object(self, obj):
        if not isinstance(obj, ODBObject):
            raise TypeError, "can only reduce isntances of ODBObject"
        if obj._p_id not in self._cache:
            raise TransactionError, "object %r not owned by transaction %r" % (obj, self)
        dct = obj.__get_odb_state__()
        cls = obj.__class__
        if _use_object_cache and obj._p_id in _object_cache:
            _object_cache[obj._p_id] = (cls,dct)
        return (cls,dct)

    def _pickle(self, obj):
        reduced = self._reduce_object(obj)
        return cPickle.dumps(reduced, _pickle_proto)
        
    def _new_object(self, obj):
        assert self._commiting
        if not isinstance(obj, ODBObject):
            raise TypeError, "can only register isntances of ODBObject with the ODB"
        if _storage is None:
            raise NotInitialised
        if obj._p_deleted:
            return
        if "_p_id" in obj.__dict__:
            return obj._p_id
        id = _storage.new_id()
        if _debug_info:
            print "new object %r gets id %i" % (obj, id)
        obj._p_id = id
        obj._p_changed = True
        self._cache[id] = obj
        self._write_buffer[id] = self._pickle(obj)
        return id

    def _store_object(self, obj):
        assert self._commiting
        if isinstance(obj, ODBProxy):
            return obj._p_id
        if not isinstance(obj, ODBObject):
            raise InvalidObject, "Cannot store object of type %s" % type(obj)
        if obj._p_deleted:
            return
        if "_p_id" in obj.__dict__:
            id = obj._p_id
            if not ('p_changed' in obj.__dict__) or obj._p_changed:
                if _debug_info:
                    print "putting object %i to write buffer" % id
                self._write_buffer[id] = self._pickle(obj)
            else:
                if _debug_info:
                    print "object %i hasn't changed, not saving" % id
            obj._p_changed = False
            return id
        return self._new_object(obj)
        
    def _flatten_object(self, obj):
        assert self._commiting
        if isinstance(obj, ODBProxy):
            return obj._p_id
        if obj._p_deleted:
            return -1
        if not isinstance(obj, ODBObject):
            raise InvalidObject, "Cannot flatten object of type %s" % type(obj)
        self._store_object(obj)
        id = obj._p_id
        if _debug_info:
            print "flatting object %i to a proxy" % id
        obj.__clear_odb_state__()
        obj.__dict__.clear()    
        obj.__dict__.update({'_p_id':id})
        obj.__class__ = ODBProxy
        return id

    def _load_state(self, id):
        if _use_data_cache:
            if id in _storage_cache: ## TODO: probably faster with try-catch
                pckl = _storage_cache[id]
            else:            
                pckl = _storage.get_pickle(id)
                _storage_cache[id] = pckl
        else:
            pckl = _storage.get_pickle(id)            
            
        ##cls,dct = _storage[id]
        return cPickle.loads(pckl)

    def _restore_proxy(self, proxy):
        if not isinstance(proxy, ODBProxy):
            raise TypeError, "tried to restore a non-proxy object"        
        id = proxy._p_id
        if id in self._cache and not isinstance(self._cache[id], ODBProxy):
            if _debug_info:
                print "getting object %i from transaction cache" % id
            return self._cache[id]
        if _debug_info:
            print "restoring object %i" % id

        if _use_object_cache and id in _object_cache:
            if _debug_info:
                print "...from object cache"
            cls,dct = _object_cache[id]
        else:
            cls,dct = self._load_state(id)

        obj = cls.__new__(cls)
        obj.__set_odb_state__(dct)        
        obj.__dict__['_p_changed'] = 0
        obj.__dict__['_p_id'] = id
        obj.__dict__['_p_deleted'] = False
        self._cache[id] = obj
        if _use_object_cache:
            _object_cache[id] = cls,dct
        if _debug_info:
            print "...got object %r" % obj
        if id in self._other_writes:
            ## object read after another transaction commited it, so it is up-to-date
            del self._other_writes[id]
        return obj

    def _restore_object(self, id):
        global _transaction
        _transaction = self
        return _restore_object(id)


def _r(id):
    if _storage is None:
        raise NotInitialised
    if _transaction is None:
        if not _auto_transaction:
            raise NoTransaction
        new_transaction()
    if id not in _storage:
        if _debug_info:
            print "Object %i has been deleted!" % id
        return None
##    try:
##        obj = _transaction._cache[id]
##        if _debug_info:
##            print "restoring object %i from cache" % id        
##    except KeyError:
    if _debug_info:
        print "creating proxy for object %i" % id
    obj = ODBProxy()
    obj._p_id = id
    if id not in _transaction._cache:
        _transaction._cache[id] = obj
    return obj
_restore_object = _r
_r.__safe_for_unpickling__ = 1

def _none():
    return None
_none.__safe_for_unpickling__ = 1


class ODBProxy(object):
    _members = '_p_id', '__getstate__','__setstate__','__reduce__','_p_restore','__reduce_ex__','__class__'

    def _p_restore(self):
        if _transaction is None:
            if not _auto_transaction:
                raise NoTransaction
            new_transaction()
        if not _auto_wake and (self._p_id not in _transaction._cache \
           or isinstance(_transaction._cache[self._p_id], ODBProxy)):
            raise ODBError, "Accessing an hibernating object. Call wake first"
        return _transaction._restore_proxy(self)

    def __reduce__(self):
        return (_r, (self._p_id,))

    def __getattribute__(self, name):
        if name in ODBProxy._members:
            return object.__getattribute__(self, name)
        if _debug_info:
            print "getting attribute %s from proxy" % name
        state = self._p_restore()
        return getattr(state, name)

    def __setattr__(self, name, value):
        if name in ODBProxy._members:
            object.__setattr__(self,name,value)
            return
        state = self._p_restore()
        setattr(state, name, value)

    def __delattr__(self, name):
        state = self._p_restore()
        delattr(state, name)

    def __hasattr__(self, name):
        state = self._p_restore()
        return hasattr(state, name)

    def __getitem__(self, name):
        state = self._p_restore()
        return state.__getitem__(name)

    def __setitem__(self, name, value):
        state = self._p_restore()
        state.__setitem__(name, value)

    def __contains__(self, name):
        state = self._p_restore()
        return state.__contains__(name)

    def __delitem__(self, name):
        state = self._p_restore()
        state.__delitem__(name)

    def __iter__(self):
        state = self._p_restore()
        return iter(state)

    def __hash__(self):
        state = self._p_restore()
        return hash(state)

    def __str__(self):
        state = self._p_restore()
        return str(state)

    def __repr__(self):
        state = self._p_restore()
        return repr(state)

    def __cmp__(self, other):
        state = self._p_restore()
        return cmp(state, other)

    def __len__(self):
        state = self._p_restore()
        return len(state)
   
class ODBObject(object):
    _p_deleted = False
    _p_changed = False
    
    def __reduce__(self):
        #print "reducing %r" % self
        if '_p_deleted' in self.__dict__ and self._p_deleted:
            return (_none, ())
        if _transaction is None:
            raise NoTransaction
        if not '_p_id' in self.__dict__:
            _transaction._new_object(self)
            #print "new object:%s" % self._p_id
        else:
            #print "old object:%s" % self._p_id
            if self._p_id not in _transaction._cache:
                raise TransactionError, "object in wrong transaction"
        return (_r, (self._p_id,))

    def __get_odb_state__(self):
        d = {}
        d.update(self.__dict__)
        if '_p_id' in d: del d['_p_id']
        if '_p_changed' in d: del d['_p_changed']
        if '_p_deleted' in d: del d['_p_deleted']
        return d

    def __set_odb_state__(self, state):
        self.__dict__.clear()
        self.__dict__.update(state)

    def __clear_odb_state__(self):
        pass

    def __odb_changed__(self):
        ## TODO: copy-on-write
        if self._p_changed: return
        if _use_object_cache and "_p_id" in self.__dict__ and self._p_id in _object_cache:
            if _transaction is None:
                if not _auto_transaction:
                    raise NoTransaction
                new_transaction()
                _transaction._cache[self._p_id] = self
            cls,dct = _transaction._load_state(self._p_id)
            id = self._p_id
            deleted = self._p_deleted
            self.__set_odb_state__(dct)
            self.__dict__['_p_id'] = id
            self.__dict__['_p_deleted'] = deleted
        object.__setattr__(self, "_p_changed", True)

    def __setitem__(self, key, value):
        self.__odb_changed__()
        object.__setitem__(self, key, value)

    def __setattr__(self, key, value):
        if key.startswith("_p_") or key.startswith("__"):
            pass
        else:
            self.__odb_changed__()
        object.__setattr__(self, key, value)
  
    def __delitem__(self, key):
        self.__odb_changed__()
        object.__delitem__(self, key)

    def __delattr__(self, key):
        self.__odb_changed__()
        object.__delattr__(self, key)
        
    def type(self):
        return type(self)

    def isinstance(self, cls):
        return isinstance(self, cls)

class _NoParam(object): pass

class ODBList(ODBObject):
    def __init__(self, items=None):
        if items is None:
            self.list = []
        else:
            self.list = list(items)
    
    def __setitem__(self, index, value):
        self.__odb_changed__()
        self.list[index] = value
    
    def __delitem__(self, index):
        self.__odb_changed__()
        del self.list[index]

    def insert(self, index, obj):
        self.__odb_changed__()
        self.list.insert(index, obj)

    def append(self, obj):
        self.__odb_changed__()
        self.list.append(obj)

    def pop(self, index=None):
        self.__odb_changed__()
        if index is None:
            return self.list.pop()
        self.list.pop(index)

    def sort(self):
        self.__odb_changed__()
        self.list.sort()

    def __getitem__(self, index):
        return self.list[index]

    def __iter__(self):
        return iter(self.list)

    def __contains__(self, item):
        return item in self.list

    def __len__(self):
        return len(self.list)

class ODBDict(ODBObject):
    
    def __init__(self, *arg):
        self.dict = dict(*arg)
    
    def __setitem__(self, key, value):
        self.__odb_changed__()
        self.dict[key] = value
    
    def __delitem__(self, key):
        self.__odb_changed__()
        del self.dict[key]

    def setdefault(self, key, value):
        self.__odb_changed__()
        self.dict.setdefault(key, value)
    
    def clear(self):
        self.__odb_changed__()
        self.dict.clear(self)

    def update(self, src):
        self.__odb_changed__()
        self.dict.update(self, src)

    def get(self, key, default=_NoParam):
        if default is _NoParam:
            return self.dict.get(key)
        return self.dict.get(key, default)

    def pop(self, key, default=_NoParam):
        self.__odb_changed__()
        if default is _NoParam:
            return self.dict.pop(key)
        return self.dict.pop(key, default)
  
    def __getitem__(self, key):
        return self.dict[key]

    def __iter__(self):
        return iter(self.dict)

    def __contains__(self, key):
        return key in self.dict

    def __len__(self):
        return len(self.dict)

    def items(self):
        return self.dict.items()

    def keys(self):
        return self.dict.keys()

    def values(self):
        return self.dict.values()

    def iteritems(self):
        return self.dict.iteritems()

    def iterkeys(self):
        return self.dict.iterkeys()

    def itervalues(self):
        return self.dict.itervalues()

class ODBObjectVersioned(ODBObject):
    persistenceVersion = 0

    def __get_odb_state__(self):
        d=ODBObject.__get_odb_state__(self)
        d['persistenceVersion']=self.__class__.persistenceVersion

        print '__get_odb_state__', d
        
        return d

    def __set_odb_state__(self, state):
        ODBObject.__set_odb_state__(self, state)

        curVer=state.get('persistenceVersion', 0)

        ## print 'preVer', curVer, self.__class__.persistenceVersion

        if curVer < self.__class__.persistenceVersion:
            while curVer < self.__class__.persistenceVersion:
                curVer += 1
                method=self.__class__.__dict__.get('upgradeToVersion%d' % curVer, None)
                if method:
                    method(self)
