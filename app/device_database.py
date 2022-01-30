import os
import app
import copy
import json

_ydoc = None
db_file = app.config_path / 'device-config.json'
if db_file.exists():
    with open(db_file, 'r', encoding='utf-8') as f:
        try:
            _ydoc = json.load(f)
        except json.JSONDecodeError:
            f.seek(0)
            jdoc = f.read().strip()
            if not jdoc:
                _ydoc = None
            else:
                raise
            
if _ydoc is None:
    _ydoc = {'$schema':'device-config.schema.json'}

def _set_dirty():
    global _dirty
    _dirty = True

def _save():
    global _dirty
    if _dirty:
        swpfile = db_file + '.saving'
        with open(swpfile, 'w', encoding='utf-8') as f:
            json.dump(_ydoc, f, indent=2)
        os.replace(swpfile, db_file)
        dirty = False

class DeviceConfig:
    def __init__(self, name, source):
        self._name = name
        self._source = source
        if source is not None:
            self._mapping = copy.deepcopy(source)
        else:
            self._mapping = {}
        self._ops = []

    def __getitem__(self, name):
        if name not in self._mapping:
            raise KeyError(name)
        return self._mapping[name]

    def get(self, key, default):
        return self._mapping.get(key, default)

    def __contains__(self, name):
        return name in self._mapping

    def __setitem__(self, name, value):
        _set_dirty()
        value = copy.deepcopy(value)
        self._mapping[name] = value
        def op():
            self._source[name] = value
        self._ops.append(op)

    def __delitem__(self, name):
        del self._mapping[name]

    def __dict__(self):
        return copy.deepcopy(dict(self._mapping))

    def __repr__(self):
        return 'DeviceConfig[%r, %r]' % (self._name, self._mapping)

    def is_new_record(self):
        return self._source is None

    def save(self):
        if self._source is None:
            _ydoc[self._name] = copy.deepcopy(self._mapping)
        else:
            for op in self._ops:
                op()
        self._ops.clear()
        _save()
    
def get_device(name):
    if name in _ydoc:
        return DeviceConfig(name, _ydoc[name])
    else:
        record = DeviceConfig(name, None)
        return record

def contains(name):
    return name in _ydoc
