##
## ODB2 - Pure Python object database
## Copyright (C) 2004 Sami Hangaslammi (shang@jyu.fi)
##

import time

class TrackingDict(dict):
    def __init__(self, *args, **kw):
        dict.__init__(self, *args, **kw)
        self._last_access = {}

    def __getitem__(self, key):
        self._last_access[key] = time.time()
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        self._last_access[key] = time.time()
        return dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        del self._last_access[key]
        return dict.__delitem__(self, key)

    def setdefault(self, key, value):
        self._last_access[key] = time.time()
        return dict.setdefault(self, key, value)

    def del_old(self, timelimit):
        limit = time.time() - timelimit
        deletions = [key for key,t in self._last_access.iteritems()
                     if t < limit]
        map(self.__delitem__, deletions)

    def clear(self):
        dict.clear(self)
        self._last_access.clear()
