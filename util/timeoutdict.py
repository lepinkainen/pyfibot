
import time
from threading import Thread, RLock

class _CleanupThread(Thread):
    def __init__(self, d, pollinterval):
        Thread.__init__(self)
        self.d = d
        self.interval = pollinterval
        self.setDaemon(True)
        self.running = True

    def run(self):
        while self.running:
            time.sleep(self.interval)
            self.d.cleanup()

    def stop(self):
        self.running = False

class TimeoutDict(dict):
    def __init__(self, timeout=0, pollinterval=10.0):
        dict.__init__(self)
        self._timeout = timeout
        self._lastchange = {}
        self._lock = RLock()

        if timeout > 0:
            self._thread = _CleanupThread(self, pollinterval)
            self._thread.start()
        else:
            self._thread = None

    def __setitem__(self, key, value):
        self._lock.acquire()
        try:
            dict.__setitem__(self, key, value)
            self._lastchange[key] = time.time()
        finally:
            self._lock.release()

    def update(self, src):
        for k,v in src.iteritems():
            self[k] = v

    def __delitem__(self, key):
        self._lock.acquire()
        try:
            dict.__delitem__(self, key)
            del self._lastchange[key]
        finally:
            self._lock.release()

    def __del__(self):
        if self._thread is not None:
            self._thread.stop()

    def cleanup(self, timeout=None):
        self._lock.acquire()
        try:
            if timeout is None:
                timeout = self._timeout
            current = time.time()
            for k,t in self._lastchange.items():
                if current > t + timeout:
                    del self[k]
        finally:
            self._lock.release()
