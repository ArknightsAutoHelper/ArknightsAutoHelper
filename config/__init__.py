# from config.shell_log import ShellColor, BufferColor
# from config.developer_config import *
# from config.common_config import SCREEN_SHOOT_SAVE_PATH, STORAGE_PATH, CONFIG_PATH

import logging.config
import os
import shutil
import sys

if sys.version_info[:2] >= (3, 8):
    from collections.abc import Mapping
else:
    from collections import Mapping

import ruamel.yaml

yaml = ruamel.yaml.YAML()
bundled = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
use_state_separation = None
if bundled:
    root = sys._MEIPASS
    # FIXME: macOS app bundle outside /Applications
    config_template_path = os.path.join(root, 'config')
else:
    config_template_path = os.path.realpath(os.path.dirname(__file__))
    root = os.path.realpath(os.path.join(config_template_path, '..'))

try:
    if not bundled and os.path.exists(os.path.join(root, '.git')):
        from .scm_version import version
    else:
        from .release_info import version
except ImportError:
    version = 'UNKNOWN'

if use_state_separation is None:
    # TODO: check for writable base directory
    use_state_separation = False

if use_state_separation:
    system = sys.platform
    if system == "win32":
        # TODO: windows user data dir
        platform_appdata_path = os.getenv('LOCALAPPDATA')
    elif system == 'darwin':
        platform_appdata_path = os.path.expanduser('~/Library/Preferences')
    else:
        platform_appdata_path = os.getenv('XDG_CONFIG_HOME', os.path.expanduser("~/.config"))
    writable_root = os.path.join(platform_appdata_path, 'ArknightsAutoHelper')
else:
    writable_root = root

background = False
ADB_ROOT = os.path.join(root, 'ADB', sys.platform)
SCREEN_SHOOT_SAVE_PATH = os.path.join(writable_root, 'screenshot')
CONFIG_PATH = os.path.join(writable_root, 'config')
cache_path = os.path.join(writable_root, 'cache')
extra_items_path = os.path.join(writable_root, 'extra_items')
config_file = os.path.join(CONFIG_PATH, 'config.yaml')
config_template = os.path.join(config_template_path, 'config-template.yaml')
logging_config_file = os.path.join(CONFIG_PATH, 'logging.yaml')
logging_config_template = os.path.join(config_template_path, 'logging.yaml')
logs = os.path.join(writable_root, 'log')
use_archived_resources = not os.path.isdir(os.path.join(root, 'resources'))
if use_archived_resources:
    resource_archive = os.path.join(root, 'resources.zip')
    sys.path.append(resource_archive)
    resource_root = os.path.join(root, 'resources.zip', 'resources')
else:
    resource_archive = None
    resource_root = os.path.join(root, 'resources')

os.makedirs(SCREEN_SHOOT_SAVE_PATH, exist_ok=True)
os.makedirs(CONFIG_PATH, exist_ok=True)
os.makedirs(cache_path, exist_ok=True)
os.makedirs(extra_items_path, exist_ok=True)
os.makedirs(logs, exist_ok=True)

dirty = False

def _create_config_file():
    with open(config_template, 'r', encoding='utf-8') as f:
        loader = yaml.load_all(f)
        next(loader) # discard first document (used for comment)
        ydoc = next(loader)
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(ydoc, f)

if not os.path.exists(config_file):
    _create_config_file()

with open(config_file, 'r', encoding='utf-8') as f:
    _ydoc = yaml.load(f)


def _get_instance_id_win32():
    import ctypes
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    CreateMutex = k32.CreateMutexW
    CloseHandle = k32.CloseHandle
    ERROR_ALREADY_EXISTS = 183
    from zlib import crc32
    path_hash = crc32(os.path.realpath(config_file).encode())
    i = 0
    while True:
        name = 'Global\\ArknightsAutoHelper.%08X.%d' % (path_hash, i)
        import ctypes
        mutex = ctypes.c_void_p(CreateMutex(None, True, name))
        err = ctypes.get_last_error()

        if not mutex:
            raise OSError("CreateMutex failed")

        if err == ERROR_ALREADY_EXISTS:
            CloseHandle(mutex)
            i += 1
            continue  # try next index

        import atexit
        atexit.register(lambda: CloseHandle(mutex))

        return i


def _get_instance_id_posix():
    i = 0
    while True:
        try:
            if i == 0:
                filename = os.path.join(logs, 'ArknightsAutoHelper.log')
            else:
                filename = os.path.join(logs, 'ArknightsAutoHelper.%d.log' % i)
            f = open(filename, 'a+b')
            f.seek(0)
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            import atexit
            def fini(lockfile):
                if lockfile is not None:
                    lockfile.close()
            atexit.register(fini, f)
            return i
        except OSError:
            i += 1


def _get_instance_id():
    if os.name == 'nt':
        return _get_instance_id_win32()
    else:
        return _get_instance_id_posix()


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
# enable_adb_host_auto_detect = get('device/enable_adb_host_auto_detect', True)
# ADB_HOST = get('device/adb_connect', '127.0.0.1:7555')
ArkNights_PACKAGE_NAME = get('device/package_name', 'com.hypergryph.arknights')
ArkNights_ACTIVITY_NAME = get('device/activity_name', 'com.u8.sdk.U8UnityContext')

engine = get('ocr/engine', 'auto')
enable_baidu_api = get('ocr/baidu_api/enabled', False)
APP_ID = get('ocr/baidu_api/app_id', 'AAAZZZ')
API_KEY = get('ocr/baidu_api/app_key', 'AAAZZZ')
SECRET_KEY = get('ocr/baidu_api/app_secret', 'AAAZZZ')
reporter = get('reporting/enabled', False)

_instanceid = None
logfile = None

def get_instance_id():
    global _instanceid, logfile
    if _instanceid is not None:
        return _instanceid

    _instanceid = _get_instance_id()
    if _instanceid == 0:
        logfile = os.path.join(logs, 'ArknightsAutoHelper.log')
    else:
        logfile = os.path.join(logs, 'ArknightsAutoHelper.%d.log' % _instanceid)


    return _instanceid

logging_enabled = False

def enable_logging():
    global logging_enabled
    if logging_enabled:
        return
    get_instance_id()
    old_handlers = logging.root.handlers[:]
    if not os.path.exists(logging_config_file):
        shutil.copy2(logging_config_template, logging_config_file)
    with open(logging_config_file, 'r', encoding='utf-8') as f:
        logging.config.dictConfig(yaml.load(f))
    for h in old_handlers:
        logging.root.addHandler(h)
    logging.debug('ArknightsAutoHelper version %s', version)
    import coloredlogs
    coloredlogs.install(
        fmt=' Ξ %(message)s',
        #fmt=' %(asctime)s ! %(funcName)s @ %(filename)s:%(lineno)d ! %(levelname)s # %(message)s',
        datefmt='%H:%M:%S',
        level_styles={'warning': {'color': 'yellow'}, 'error': {'color': 'red'}},
        level='INFO')
    logging_enabled = True
    if os.path.getmtime(config_file) < os.path.getmtime(config_template):
        logging.warning('配置文件模板 config-template.yaml 已更新，请检查配置文件 config.yaml 是否需要更新')
