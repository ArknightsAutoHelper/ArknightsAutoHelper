# from config.shell_log import ShellColor, BufferColor
# from config.developer_config import *
# from config.common_config import SCREEN_SHOOT_SAVE_PATH, STORAGE_PATH, CONFIG_PATH

import sys
import os
import shutil
from collections import Mapping
import logging.config
import ruamel.yaml
from .version import version
yaml = ruamel.yaml.YAML()


CONFIG_PATH = os.path.realpath(os.path.dirname(__file__))
root = os.path.realpath(os.path.join(CONFIG_PATH, '..'))
ADB_ROOT = os.path.join(root, 'ADB', sys.platform)
SCREEN_SHOOT_SAVE_PATH = os.path.join(root, 'screen_shoot')
STORAGE_PATH = os.path.join(root, 'storage')
config_file = os.path.join(CONFIG_PATH, 'config.yaml')
config_template = os.path.join(CONFIG_PATH, 'config-template.yaml')
logging_config_file = os.path.join(CONFIG_PATH, 'logging.yaml')
logs = os.path.join(root, 'log')
if not os.path.exists(logs):
    os.mkdir(logs)
logfile = os.path.join(root, 'log', 'ArknightsAutoHelper.log')

dirty = False

if not os.path.exists(config_file):
    shutil.copy(config_template, config_file)

with open(config_file, 'r', encoding='utf-8') as f:
    _ydoc = yaml.load(f)


def _set_dirty():
    global dirty
    dirty = True


def save():
    global dirty
    if dirty:
        swpfile = config_file + '.saving'
        with open(swpfile, 'w', encoding='utf-8') as f:
            yaml.dump(_ydoc, f)
        os.replace(swpfile, config_file)
        dirty = False


def _dig_mapping(dig, create_parent=False):
    if isinstance(dig, str):
        dig = dig.split('/')
    parent_maps = dig[:-1]
    current_map = _ydoc
    i = 0
    for k in parent_maps:
        if k not in current_map:
            if not create_parent:
                raise KeyError(dig)
            current_map[k] = {}
            _set_dirty()
        current_map = current_map[k]
        if not isinstance(current_map, Mapping):
            raise TypeError('config key %s is not a mapping' % '/'.join(dig[:i + 1]))
        i += 1
    k = dig[-1]
    return current_map, k


_default_not_set = object()


def get(dig, default=_default_not_set, set_default=False):
    try:
        current_map, k = _dig_mapping(dig, create_parent=set_default)
    except (KeyError, TypeError):  # thrown when create_parent is False
        if default is _default_not_set:
            raise
        return default
    if k not in current_map:
        if default is _default_not_set:
            raise KeyError(dig)
        if set_default:
            current_map[k] = default
            _set_dirty()
        return default
    return current_map[k]


def set(dig, value):
    current_map, k = _dig_mapping(dig, create_parent=True)
    current_map[k] = value
    _set_dirty()


ADB_SERVER = (lambda host, portstr: (host, int(portstr)))(
    # attempt to not pollute global namespace
    *(get('device/adb_server', '127.0.0.1:5037').rsplit(':', 1))
)
enable_adb_host_auto_detect = get('device/enable_adb_host_auto_detect', True)
ADB_HOST = get('device/adb_connect', '127.0.0.1:7555')
ArkNights_PACKAGE_NAME = get('device/package_name', 'com.hypergryph.arknights')
ArkNights_ACTIVITY_NAME = get('device/activity_name', 'com.u8.sdk.U8UnityContext')

engine = get('ocr/engine', 'auto')
enable_baidu_api = get('ocr/baidu_api/enabled', False)
APP_ID = get('ocr/baidu_api/app_id', 'AAAZZZ')
API_KEY = get('ocr/baidu_api/app_key', 'AAAZZZ')
SECRET_KEY = get('ocr/baidu_api/app_secret', 'AAAZZZ')

reporter = get('reporting/enabled', False)

with open(logging_config_file, 'r', encoding='utf-8') as f:
    logging.config.dictConfig(yaml.load(f))
del f
