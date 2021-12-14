import ctypes

class ExportObject:
    def __init__(self, obj, *interfaces):
        self.interfaces = interfaces
        self.vtbls = []
        self.vtbl_array = ctypes.c_void_p * len(self.vtbls)
        self.obj = obj
        self._refcnt = 1
        ctypes.pythonapi.Py_IncRef(ctypes.py_object(self))

    def AddRef(self):
        self._refcnt += 1
        return self._refcnt

    def Release(self):
        self._refcnt -= 1
        if self._refcnt == 0:
            ctypes.pythonapi.Py_DecRef(ctypes.py_object(self))
        return self._refcnt
