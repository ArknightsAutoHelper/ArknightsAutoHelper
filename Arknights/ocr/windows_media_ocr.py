
try:
    from .windows_media_ocr_impl import recognize
    check_supported = lambda: True
    info = None
except Exception as e:
    check_supported = lambda: False
    def recognize(*args, **kwargs):
        raise NotImplementedError
    info = e
