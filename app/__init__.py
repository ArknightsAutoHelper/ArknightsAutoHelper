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

# setup app paths

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
        from app.scm_version import version
    else:
        from app.release_info import version
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
screenshot_path = os.path.join(writable_root, 'screenshot')
config_path = os.path.join(writable_root, 'config')
cache_path = os.path.join(writable_root, 'cache')
extra_items_path = os.path.join(writable_root, 'extra_items')
config_file = os.path.join(config_path, 'config.yaml')
config_template = os.path.join(config_template_path, 'config-template.yaml')
logging_config_file = os.path.join(config_path, 'logging.yaml')
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
vendor_root = os.path.join(root, 'vendor')
tessdata_prefix = os.path.join(root, 'tessdata')


##### end of paths


os.makedirs(screenshot_path, exist_ok=True)
os.makedirs(config_path, exist_ok=True)
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

from . import schema
config = schema.root(_ydoc)

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

##### Legacy config values

ADB_SERVER = (lambda host, portstr: (host, int(portstr)))(
    # attempt to not pollute global namespace
    *(config.devices.adb_server.rsplit(':', 1))
)


##### End of Legacy config values


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


def get_vendor_path(name):
    import platform
    base = os.path.join(vendor_root, name)
    system = platform.system().lower()
    arch = platform.machine().lower()
    if system:
        if arch :
            path = os.path.join(base, f'{system}_{arch}')
            if os.path.isdir(path):
                return path
        path = os.path.join(base, system)
        if os.path.isdir(path):
            return path
    if os.path.isdir(base):
        return base
    raise FileNotFoundError(base)

class _FixedSpecFinder:
    def __init__(self, name, spec):
        self.name = name
        self.spec = spec

    def find_spec(self, fullname, path, target=None):
        if fullname == self.name:
            return self.spec
        return None
    
    def __repr__(self):
        return f'{self.__class__.__qualname__}({self.name!r}, {self.spec!r})'

def require_vendor_lib(fullname, base_path_relative_to_vendor):
    import importlib.machinery
    if bundled:
        importlib.import_module(fullname)
        return
    if fullname in sys.modules:
        return
    path = os.path.join(vendor_root, base_path_relative_to_vendor)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    spec = importlib.machinery.PathFinder.find_spec(fullname, [path] + sys.path)
    if spec is None:
        raise ModuleNotFoundError(fullname)
    sys.meta_path.insert(0, _FixedSpecFinder(fullname, spec))
    # not importing then removing from sys.meta_path, in case of lazy loading
    # importlib.import_module(fullname)
    # sys.meta_path.pop()


