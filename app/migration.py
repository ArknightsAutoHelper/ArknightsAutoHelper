import logging
import contextlib
from collections.abc import Mapping
from typing import Sequence
from . import schema, schemadef
logger = logging.getLogger(__name__)

_migrate_actions = {}

def migrate_from(version):
    def decorator(f):
        _migrate_actions[version] = f
        return f
    return decorator

def migrate(ydoc: Mapping):
    old_version = ydoc.get('__version__', None)
    while old_version != schema.root.__version__:
        action = _migrate_actions.get(old_version, None)
        if action is None:
            raise ValueError(f'No migration from version {old_version}')
        ydoc = action(ydoc)
        old_version = ydoc.get('__version__', None)
    return ydoc

@migrate_from(None)
def migrate_from_legacy(ydoc: Mapping):
    logger.info('Migrating from legacy config schema')
    ydoc['combat'] = schemadef._generate_default_store(schema.root.combat)
    ydoc['stage_navigator'] = schemadef._generate_default_store(schema.root.stage_navigator)
    ydoc['grass_on_aog'] = schemadef._generate_default_store(schema.root.grass_on_aog)
    with contextlib.suppress(KeyError, AttributeError):
        if isinstance(ydoc['device']['extra_enumerators'], Mapping) and 'bluestacks_hyperv' in ydoc['device']['extra_enumerators']:
            ydoc['device']['extra_enumerators']['bluestacks_hyperv'] = True
    with contextlib.suppress(KeyError, AttributeError):
        if ydoc['behavior'].get('refill_ap_with_item', False) or ydoc['behavior'].get('refill_ap_with_originium', False):
            logger.warning('不再支持通过设置 behavior.refill_ap_with_item 和 behavior.refill_ap_with_originium 来控制自动回复体力，请在每次作战时通过 GUI 或命令行设置。')
    with contextlib.suppress(KeyError, AttributeError):
        old_mistaken_delegation = ydoc['behavior']['mistaken_delegation']
        if isinstance(old_mistaken_delegation, Mapping):
            ydoc['combat']['mistaken_delegation'] = old_mistaken_delegation
            del ydoc['behavior']
    try:
        old_ocr = ydoc['ocr']
        if isinstance(old_ocr, Mapping):
            old_ocr['backend'] = old_ocr['engine']
            del old_ocr['engine']
            old_prefer_svm = old_ocr['prefer_svm'].get('stage_prefer_svm', True)
            if old_prefer_svm:
                ydoc['stage_navigator']['ocr_backend'] = 'svm'
            else:
                ydoc['stage_navigator']['ocr_backend'] = 'dnn'
    except:
        ydoc['ocr'] = schemadef._generate_default_store(schema.root.ocr)
    with contextlib.suppress(KeyError, AttributeError):
        old_reporting = ydoc['reporting']
        if isinstance(old_reporting, Mapping):
            ydoc['combat']['penguin_stats']['enabled'] = old_reporting['enabled']
            ydoc['combat']['penguin_stats']['uid'] = old_reporting['penguin_stats_uid']
            ydoc['combat']['penguin_stats']['report_special_item'] = old_reporting['report_special_item']
            del ydoc['reporting']
    with contextlib.suppress(KeyError, AttributeError):
        old_grass_on_aog_exclude = ydoc['addons']['grass_on_aog']['exclude_names']
        if isinstance(old_grass_on_aog_exclude, Sequence):
            ydoc['grass_on_aog']['exclude'] = old_grass_on_aog_exclude
    ydoc['__version__'] = 1
    return ydoc

@migrate_from(1)
def migrate_from_1(ydoc: Mapping):
    logger.info('Migrating from config schema version 1')
    with contextlib.suppress(KeyError, AttributeError):
        if ydoc['ocr']['backend'] == 'windows_media_ocr':
            logger.warn('Windows OCR 因识别率问题已移除，设置更改为自动选择（当前仅支持 Tesseract）。')
            ydoc['ocr']['backend'] = 'auto'
    ydoc['__version__'] = 2
    return ydoc

@migrate_from(2)
def migrate_from_2(ydoc: Mapping):
    ydoc['__version__'] = 3
    return ydoc

@migrate_from(3)
def migrate_from_3(ydoc: Mapping):
    logger.info('Migrating from config schema version 3')
    import app
    import os
    try:
        os.unlink(app.config_path / 'device-config.json')
    except:
        pass
    ydoc['__version__'] = 4
    return ydoc

@migrate_from(4)
def migrate_from_4(ydoc: Mapping):
    logger.info('Migrating from config schema version 4')
    with contextlib.suppress(KeyError, AttributeError):
        if ydoc['device']['cache_screenshot']:
            ydoc['device']['screenshot_rate_limit'] = -1
            del ydoc['device']['cache_screenshot']
    # with contextlib.suppress(KeyError, AttributeError):
    ydoc['device']['defaults'] = schemadef._generate_default_store(schema.root.device.type.defaults, 4)
    with contextlib.suppress(KeyError, AttributeError):
        if ydoc['device']['compat_screenshot']:
            ydoc['device']['defaults']['screenshot_method'] = 'aosp-screencap'
            ydoc['device']['defaults']['aosp_screencap_encoding'] = 'png'
            del ydoc['device']['compat_screenshot']
    with contextlib.suppress(KeyError, AttributeError):
        if not ydoc['device']['workaround_slow_emulator_adb']:
            ydoc['device']['defaults']['screenshot_transport'] = 'adb'
        del ydoc['device']['workaround_slow_emulator_adb']
    ydoc['__version__'] = 5
    return ydoc
