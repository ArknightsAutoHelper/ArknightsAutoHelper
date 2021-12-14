import os
if os.name == 'posix':
    from .posix import *
elif os.name == 'nt':
    from .win32 import *
else:
    raise NotImplementedError("os %s not supported" % os.name)
