import ctypes

class SizeInt32(ctypes.Structure):
    _fields_ = [('Width', ctypes.c_int32), ('Height', ctypes.c_int32)]
