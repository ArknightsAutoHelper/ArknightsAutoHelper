is_online = False
info = 'Windows.Media.Ocr'
try:
    from .windows_media_ocr_impl import Engine, check_supported

except Exception as e:
    check_supported = lambda: False
    Engine = None
