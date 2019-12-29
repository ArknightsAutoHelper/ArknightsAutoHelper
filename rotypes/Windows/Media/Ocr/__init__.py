from ctypes import c_uint32, c_bool, c_double

from rotypes.Windows.Foundation import IReference, Rect, IAsyncOperation
from rotypes.Windows.Foundation.Collections import IVectorView
from rotypes.Windows.Globalization import Language
from rotypes.Windows.Graphics.Imaging import SoftwareBitmap
from rotypes.inspectable import IInspectable
from rotypes.idldsl import define_winrt_com_method, _static_propget, _static_method, _non_activatable_init, runtimeclass
from rotypes.winstring import HSTRING


class IOcrWord(IInspectable):
    IID = '3C2A477A-5CD9-3525-BA2A-23D1E0A68A1D'


class IOcrLine(IInspectable):
    IID = '0043A16F-E31F-3A24-899C-D444BD088124'


class IOcrResult(IInspectable):
    IID = '9BD235B2-175B-3D6A-92E2-388C206E2F63'


class IOcrEngine(IInspectable):
    IID = '5A14BC41-5B76-3140-B680-8825562683AC'


class IOcrEngineStatics(IInspectable):
    IID = '5BFFA85A-3384-3540-9940-699120D428A8'


class OcrWord(runtimeclass, IOcrWord):
    pass


class OcrLine(runtimeclass, IOcrLine):
    pass


class OcrResult(runtimeclass, IOcrResult):
    pass


class OcrEngine(runtimeclass, IOcrEngine):
    __init__ = _non_activatable_init
    MaxImageDimension = _static_propget(IOcrEngineStatics, 'MaxImageDimension')
    AvailableRecognizerLanguages = _static_propget(IOcrEngineStatics, 'AvailableRecognizerLanguages')
    IsLanguageSupported = _static_method(IOcrEngineStatics, 'IsLanguageSupported')
    TryCreateFromLanguage = _static_method(IOcrEngineStatics, 'TryCreateFromLanguage')
    TryCreateFromUserProfileLanguages = _static_method(IOcrEngineStatics, 'TryCreateFromUserProfileLanguages')


define_winrt_com_method(IOcrWord, 'get_BoundingRect', propget=Rect, vtbl=6)
define_winrt_com_method(IOcrWord, 'get_Text', propget=HSTRING, vtbl=7)

define_winrt_com_method(IOcrLine, 'get_Words', propget=IVectorView(OcrWord), vtbl=6)
define_winrt_com_method(IOcrLine, 'get_Text', propget=HSTRING, vtbl=7)

define_winrt_com_method(IOcrResult, 'get_Lines', propget=IVectorView(OcrLine), vtbl=6)
define_winrt_com_method(IOcrResult, 'get_TextAngle', propget=IReference(c_double), vtbl=7)
define_winrt_com_method(IOcrResult, 'get_Text', propget=HSTRING, vtbl=8)

define_winrt_com_method(IOcrEngine, 'RecognizeAsync', SoftwareBitmap, retval=IAsyncOperation(OcrResult), vtbl=6)
define_winrt_com_method(IOcrEngine, 'get_RecognizerLanguage', propget=Language, vtbl=7)

define_winrt_com_method(IOcrEngineStatics, 'get_MaxImageDimension', propget=c_uint32, vtbl=6)
define_winrt_com_method(IOcrEngineStatics, 'get_AvailableRecognizerLanguages', propget=IVectorView(Language), vtbl=7)
define_winrt_com_method(IOcrEngineStatics, 'IsLanguageSupported', Language, retval=c_bool, vtbl=8)
define_winrt_com_method(IOcrEngineStatics, 'TryCreateFromLanguage', Language, retval=IOcrEngine, vtbl=9)
define_winrt_com_method(IOcrEngineStatics, 'TryCreateFromUserProfileLanguages', retval=IOcrEngine, vtbl=10)
