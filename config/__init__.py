# from config.shell_log import ShellColor, BufferColor
# from config.developer_config import *
# from config.common_config import SCREEN_SHOOT_SAVE_PATH, STORAGE_PATH, CONFIG_PATH

import logging.config
import os
import shutil
import sys
from collections import Mapping

import ruamel.yaml

yaml = ruamel.yaml.YAML()
bundled = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
if bundled:
    root = sys._MEIPASS
    CONFIG_PATH = os.path.join(root, 'config')
else:
    CONFIG_PATH = os.path.realpath(os.path.dirname(__file__))
    root = os.path.realpath(os.path.join(CONFIG_PATH, '..'))

if os.path.exists(os.path.join(root, '.git')):
    from .scm_version import version
else:
    from .release_info import version


ADB_ROOT = os.path.join(root, 'ADB', sys.platform)
SCREEN_SHOOT_SAVE_PATH = os.path.join(root, 'screenshot')
config_file = os.path.join(CONFIG_PATH, 'config.yaml')
config_template = os.path.join(CONFIG_PATH, 'config-template.yaml')
logging_config_file = os.path.join(CONFIG_PATH, 'logging.yaml')
logs = os.path.join(root, 'log')
if not os.path.exists(logs):
    os.mkdir(logs)

dirty = False

if not os.path.exists(config_file):
    shutil.copy(config_template, config_file)

with open(config_file, 'r', encoding='utf-8') as f:
    _ydoc = yaml.load(f)


def get_instance_id():
    i = 0
    while True:
        try:
            filename = os.path.join(logs, 'ArknightsAutoHelper.%d.lock' % i)
            f = open(filename, 'a+b')
            f.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 114514)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            import atexit
            def fini(lockfile, lockfilename):
                if lockfile is not None:
                    lockfile.close()
                    os.unlink(lockfilename)
            atexit.register(fini, f, filename)
            return i
        except OSError:
            i += 1


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


instanceid = get_instance_id()
if instanceid == 0:
    logfile = os.path.join(root, 'log', 'ArknightsAutoHelper.log')
else:
    logfile = os.path.join(root, 'log', 'ArknightsAutoHelper.%d.log' % instanceid)

with open(logging_config_file, 'r', encoding='utf-8') as f:
    logging.config.dictConfig(yaml.load(f))
del f
logging.debug('ArknightsAutoHelper version %s', version)
