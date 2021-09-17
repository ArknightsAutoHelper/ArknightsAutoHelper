try:
    from .libtesseract import *
except Exception:
    try:
        from .cli import *
    except Exception:
        info = 'tesseract (ERROR)'
        get_version = lambda: None
        check_supported = lambda: False
        is_online = False
        Engine = None
