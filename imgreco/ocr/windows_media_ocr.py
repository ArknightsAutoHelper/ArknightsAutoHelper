is_online = False
info = 'Windows.Media.Ocr'
try:
    from .windows_media_ocr_impl import recognize, check_supported

except Exception as e:
    check_supported = lambda: False

    def recognize(img, lang, *, hints=None):
        raise NotImplementedError
