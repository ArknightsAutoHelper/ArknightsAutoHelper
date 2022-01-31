import logging
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
    try:
        if isinstance(ydoc['device']['extra_enumerators'], Mapping) and 'bluestacks_hyperv' in ydoc['device']['extra_enumerators']:
            ydoc['device']['extra_enumerators']['bluestacks_hyperv'] = True
    except:
        pass
    try:
        old_mistaken_delegation = ydoc['behavior']['mistaken_delegation']
        if isinstance(old_mistaken_delegation, Mapping):
            ydoc['combat']['mistaken_delegation'] = old_mistaken_delegation
            del ydoc['behavior']
    except:
        pass
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
    try:
        old_reporting = ydoc['reporting']
        if isinstance(old_reporting, Mapping):
            ydoc['combat']['penguin_stats']['enabled'] = old_reporting['enabled']
            ydoc['combat']['penguin_stats']['uid'] = old_reporting['penguin_stats_uid']
            ydoc['combat']['penguin_stats']['report_special_item'] = old_reporting['report_special_item']
            del ydoc['reporting']
    except:
        pass
    try:
        old_grass_on_aog_exclude = ydoc['addons']['grass_on_aog']['exclude_names']
        if isinstance(old_grass_on_aog_exclude, Sequence):
            ydoc['grass_on_aog']['exclude'] = old_grass_on_aog_exclude
    except:
        pass
    ydoc['__version__'] = 1
    return ydoc
