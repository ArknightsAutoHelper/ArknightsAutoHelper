import pytesseract
from .common import *
import itertools


def _transpose(data):
    keys = tuple(data.keys())
    length = len(data[keys[0]])
    result = []
    for i in range(length):
        col = {}
        for k in keys:
            col[k] = data[k][i]
        result.append(col)
    return result


def _translate_bcp47(tag):
    subtags = tag.lower().split('-')

    if subtags[0] == 'en':
        return 'eng'
    elif subtags[0] == 'zh':
        if mult_in(('cn', 'sg', 'my', 'hans'), subtags[1:]):
            return 'chi_sim'
        elif mult_in(('tw', 'hk', 'mo', 'hant'), subtags[1:]):
            return 'chi_tra'

    return None


def get_version():
    try:
        import subprocess
        return subprocess.run(['tesseract', '--version'], stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines()[0]
    except:
        return False


check_supported = get_version


def _tsrc(tsobj):
    return Rect(tsobj['left'], tsobj['top'], tsobj['width'], tsobj['height'])


def _map_word(tsword):
    rc = _tsrc(tsword)
    result = OcrWord(rc, tsword['text'])
    result.conf = tsword['conf']
    return result


def _fold(tp):
    page_count = max(x['page_num']for x in tp)
    pages = []
    for page in range(1, page_count+1):
        curpage = [x for x in tp if x['page_num'] == page]
        block_count = max(x['block_num'] for x in curpage)
        blocks = []
        for block in range(1, block_count+1):
            curblock = [x for x in curpage if x['block_num'] == block]
            par_count = max(x['par_num'] for x in curblock)
            pars = []
            for par in range(1, par_count+1):
                curpar = [x for x in curblock if x['par_num'] == par]
                line_count = max(x['line_num'] for x in curpar)
                lines = []
                for line in range(1, line_count+1):
                    curline = [x for x in curpar if x['line_num'] == line]
                    words = [_map_word(w) for w in curline if w['level'] == 5]
                    ocrline = OcrLine(words)
                    ocrline.rect = _tsrc(
                        [l for l in curline if l['level'] == 4][0])
                    lines.append(ocrline)
                pars.append({'lines': lines})
            blocks.append({'pars': pars})
        pages.append({'blocks': blocks})
    return {'pages': pages}


def _to_ocrresult(f):
    return OcrResult([line for page in f['pages'] for block in page['blocks'] for par in block['pars'] for line in par['lines']])


def recognize(image, lang, *, hints=None):
    if hints == None:
        hints = []
    extra = ''
    if OcrHint.SINGLE_LINE in hints:
        extra = '--psm 7'
    elif OcrHint.SPARSE in hints:
        extra = '--psm 11'

    tslang = _translate_bcp47(lang)
    tsresult = pytesseract.image_to_data(
        image, lang=tslang, output_type='dict', config=extra)
    tpresult = _transpose(tsresult)
    foldresult = _fold(tpresult)
    flatlines = _to_ocrresult(foldresult)
    return flatlines

info = None
