import app
import copy
from app import schemadef

from app.schema import ControllerConfig

from .config_store import YamlConfigStore

db_file = app.config_path / 'device-config-v2.yaml'

store = YamlConfigStore(db_file)

class PresistentDeviceConfig(ControllerConfig):
    device_identifier: str = None
    _parent_store: YamlConfigStore = None

    def __init__(self, mapping, device_identifier: str, store: YamlConfigStore):
        super().__init__(mapping)
        self.device_identifier = device_identifier
        self._parent_store = store

    def save(self):
        self._parent_store.root[self.device_identifier] = copy.deepcopy(self._mapping)
        self._parent_store.save()


def get_device(name):
    if name in store.root:
        record_store = store.root[name]
        record = PresistentDeviceConfig(record_store, name, store)
    else:
        mapping = schemadef._generate_default_store(PresistentDeviceConfig, 2)
        mapping.update(app.config.device.defaults._mapping)
        mapping.yaml_end_comment_extend(['\n'])
        record = PresistentDeviceConfig(mapping, name, store)
    return record

def contains(name):
    return name in store.root
