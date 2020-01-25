import base64
import time
from functools import lru_cache
from io import BytesIO

#from aip import AipOcr
import requests
from config import enable_baidu_api, APP_ID, API_KEY, SECRET_KEY
from .common import *

is_online = True
info = "baidu"


def check_supported():
    if enable_baidu_api:
        return True
    else:
        return False


def _options(option):
    options = {}
    subtags = option.lower().split('-')
    if subtags[0] == 'en':
        options["language_type"] = "ENG"
    elif subtags[0] == 'zh':
        options["language_type"] = "CHN_ENG"
    return options

@lru_cache()
def _get_token():
    resp = requests.request('POST', 'https://aip.baidubce.com/oauth/2.0/token',
                     params={'grant_type': 'client_credentials', 'client_id': API_KEY, 'client_secret': SECRET_KEY})
    resp.raise_for_status()
    resp = resp.json()
    return resp['access_token']


def _basicGeneral(image, options):
    data = {}
    data['image'] = base64.b64encode(image).decode()
    data.update(options)
    t = time.monotonic()
    tdiff = t - _basicGeneral.last_call
    if tdiff < 0.3:
        # QPS limit
        time.sleep(0.3 - tdiff)
    resp = requests.post('https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic', data=data, params={'access_token': _get_token()})
    resp.raise_for_status()
    resp = resp.json()
    if 'error_code' in resp:
        raise RuntimeError(resp['error_msg'])
    _basicGeneral.last_call = time.monotonic()
    return resp

_basicGeneral.last_call = 0

def recognize(image, lang, *, hints=None):
    # line = 0
    # if hints is None:
    #     hints = []
    # if OcrHint.SINGLE_LINE in hints:
    #     line = 0
    # elif OcrHint.SPARSE in hints:
    #     # TODO
    #     line = 1
    imgbytesio = BytesIO()
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image.save(imgbytesio, format='JPEG', quality=95)
    result = _basicGeneral(imgbytesio.getvalue(), _options(lang))
    line = OcrLine([OcrWord(Rect(0, 0), x['words']) for x in result['words_result']])
    result = OcrResult([line])
    return result
