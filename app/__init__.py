# from config.shell_log import ShellColor, BufferColor
# from config.developer_config import *
# from config.common_config import SCREEN_SHOOT_SAVE_PATH, STORAGE_PATH, CONFIG_PATH
import util.early_logs

import logging.config
import os
import shutil
import sys
from pathlib import Path
from collections.abc import Mapping
from typing import Optional, Sequence

import ruamel.yaml
from . import schema

yaml = ruamel.yaml.YAML()

# setup app paths

bundled = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
use_state_separation = None
if bundled:
    root = Path(sys._MEIPASS)
    # FIXME: macOS app bundle outside /Applications
else:
    root = Path(__file__).absolute().parent.parent
config_template_path = root / 'config'

try:
    if not bundled and Path.joinpath(root, '.git').exists():
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
        platform_appdata_path = Path(os.getenv('LOCALAPPDATA'))
    elif system == 'darwin':
        platform_appdata_path = Path(os.path.expanduser('~/Library/Preferences'))
    else:
        platform_appdata_path = Path(os.getenv('XDG_CONFIG_HOME', os.path.expanduser("~/.config")))
    writable_root = platform_appdata_path / 'ArknightsAutoHelper'
else:
    writable_root = root

background = False
screenshot_path = Path.joinpath(writable_root, 'screenshot')
config_path = Path.joinpath(writable_root, 'config')
cache_path = Path.joinpath(writable_root, 'cache')
extra_items_path = Path.joinpath(writable_root, 'extra_items')
config_file = Path.joinpath(config_path, 'config.yaml')
config_template = Path.joinpath(config_template_path, 'config-template.yaml')
logging_config_file = Path.joinpath(config_path, 'logging.yaml')
logging_config_template = Path.joinpath(config_template_path, 'logging.yaml')
logs = Path.joinpath(writable_root, 'log')
use_archived_resources = not Path.joinpath(root, 'resources').is_dir()
if use_archived_resources:
    resource_archive = Path.joinpath(root, 'resources.zip')
    sys.path.append(os.fspath(resource_archive))
    resource_root = Path.joinpath(root, 'resources.zip', 'resources')
else:
    resource_archive = None
    resource_root = Path.joinpath(root, 'resources')
vendor_root = Path.joinpath(root, 'vendor')
tessdata_prefix = Path.joinpath(root, 'tessdata')


##### end of paths

dirty = False
config = schema.root()

def _save_config(store, file):
    swpfile = os.fspath(file) + '.saving'
    with open(swpfile, 'w', encoding='utf-8') as f:
        yaml.dump(store, f)
    os.replace(swpfile, config_file)

def _load_config():
    if not config_file.exists():
        config = schema.root()
        _save_config(config._store, config_file)
        return config
    with open(config_file, 'r', encoding='utf-8') as f:
        ydoc = yaml.load(f)
    config_schema_version = ydoc.get('__version__', None)
    if config_schema_version != schema.root.__version__:
        if config_schema_version is None:
            oldfile_suffix = '-legacy.bak'
        else:
            oldfile_suffix = f'-schema{config_schema_version}.bak'
        shutil.copyfile(config_file, str(config_file).removesuffix('.yaml') + oldfile_suffix)
        from .migration import migrate
        ydoc = migrate(ydoc)
        _save_config(ydoc, config_file)
    config = schema.root(ydoc)
    return config

initialized = False

def init(extra_logging_handlers=None):
    global config, initialized
    if initialized:
        return
    os.makedirs(screenshot_path, exist_ok=True)
    os.makedirs(config_path, exist_ok=True)
    os.makedirs(cache_path, exist_ok=True)
    os.makedirs(extra_items_path, exist_ok=True)
    os.makedirs(logs, exist_ok=True)
    config = _load_config()
    enable_logging(extra_logging_handlers)
    initialized = True

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
                filename = Path.joinpath(logs, 'ArknightsAutoHelper.log')
            else:
                filename = Path.joinpath(logs, 'ArknightsAutoHelper.%d.log' % i)
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
    _save_config(config._store, config_file)
    config._dirty = False


def _dig_mapping(dig, create_parent=False):
    if isinstance(dig, str):
        dig = dig.split('/')
    parent_maps = dig[:-1]
    current_map = config._store
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


def get_config_adb_server():
    host, portstr = config.device.adb_server.rsplit(':', 1)
    return host, int(portstr)


_instanceid = None
logfile = None

def get_instance_id():
    global _instanceid, logfile
    if _instanceid is not None:
        return _instanceid

    _instanceid = _get_instance_id()
    if _instanceid == 0:
        logfile = Path.joinpath(logs, 'ArknightsAutoHelper.log')
    else:
        logfile = Path.joinpath(logs, 'ArknightsAutoHelper.%d.log' % _instanceid)


    return _instanceid

logging_enabled = False

def enable_logging(extra_handlers: Optional[Sequence[logging.Handler]] = None):
    global logging_enabled
    if logging_enabled:
        return
    get_instance_id()
    old_handlers: list = logging.root.handlers[:]
    if not logging_config_file.exists():
        shutil.copy2(logging_config_template, logging_config_file)
    with open(logging_config_file, 'r', encoding='utf-8') as f:
        logging.config.dictConfig(yaml.load(f))
    if extra_handlers is not None:
        old_handlers.extend(extra_handlers)
    for h in old_handlers:
        logging.root.addHandler(h)
    early_records = util.early_logs.fetch_and_stop()
    for record in early_records:
        logging.getLogger(record.name).handle(record)
    logging.debug('ArknightsAutoHelper version %s', version)
    import coloredlogs
    coloredlogs.install(
        fmt=' Ξ %(message)s',
        #fmt=' %(asctime)s ! %(funcName)s @ %(filename)s:%(lineno)d ! %(levelname)s # %(message)s',
        datefmt='%H:%M:%S',
        level_styles={'warning': {'color': 'yellow'}, 'error': {'color': 'red'}},
        level='INFO')
    logging_enabled = True

def get_vendor_path(name):
    import platform
    base = Path.joinpath(vendor_root, name)
    system = platform.system().lower()
    arch = platform.machine().lower()
    if system:
        if arch :
            path = Path.joinpath(base, f'{system}_{arch}')
            if path.is_dir():
                return path
        path = Path.joinpath(base, system)
        if path.is_dir():
            return path
    if base.is_dir():
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
    path = Path.joinpath(vendor_root, base_path_relative_to_vendor)
    if not path.exists():
        raise FileNotFoundError(path)
    spec = importlib.machinery.PathFinder.find_spec(fullname, [os.fspath(path)] + sys.path)
    if spec is None:
        raise ModuleNotFoundError(fullname)
    sys.meta_path.insert(0, _FixedSpecFinder(fullname, spec))
    # not importing then removing from sys.meta_path, in case of lazy loading
    # importlib.import_module(fullname)
    # sys.meta_path.pop()
