
import os
from pathlib import Path

import ruamel.yaml
yaml = ruamel.yaml.YAML()

class YamlConfigStore:
    def __init__(self, filename: Path):
        self.filename = filename
        self.root = None
        self._load()
    
    def _load(self):
        if not self.filename.exists():
            self.root = self._default_root()
            return
        with open(self.filename, 'r', encoding='utf-8') as f:
            self.root = yaml.load(f)
        if self.root is None:
            self.root = self._default_root()

    def _default_root(self):
        return ruamel.yaml.CommentedMap()

    def save(self):
        swpfile = os.fspath(self.filename) + '.saving'
        with open(swpfile, 'w', encoding='utf-8') as f:
            yaml.dump(self.root, f)
        os.replace(swpfile, self.filename)
