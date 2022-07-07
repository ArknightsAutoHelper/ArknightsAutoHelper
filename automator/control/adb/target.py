from __future__ import annotations
from dataclasses import dataclass
import itertools
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import ADBServer

@dataclass
class ADBControllerTarget:
    adb_server: ADBServer
    adb_serial: Optional[str]
    description: str
    adb_address: str
    dedup_priority: int
    auto_connect_priority: int
    display_id: Optional[int] = None
    override_identifier: Optional[str] = None
    preload_device_info: Optional[dict] = None

    def create_controller(self):
        from ..ADBController import ADBController
        device = self.get_device()
        preload = self.preload_device_info
        if preload is None:
            preload = {}
        return ADBController(device, self.display_id, preload, self.override_identifier)

    def get_device(self):
        return self.adb_server.get_device(self.adb_serial or self.adb_address)

    def describe(self):
        """returns identifier, description"""
        if self.override_identifier is not None:
            identifier = self.override_identifier
            description = f'{self.description}, {self.adb_serial or self.adb_address}'
        else:
            identifier = self.adb_serial or self.adb_address
            description = self.description
        if self.display_id:
            identifier += f':display={self.display_id}'
        return identifier, description

    def __str__(self):
        identifier, description = self.describe()
        return f'{identifier} ({description})'

def dedup_targets(targets: list[ADBControllerTarget]) -> list[ADBControllerTarget]:
    """
    dedup targets by adb_address
    """
    groups = {}
    deduped = []
    for x in targets:
        key = (x.adb_address, x.display_id)
        groups.setdefault(key, []).append(x)
    for group in groups.values():
        group_targets = list(group)
        group_targets.sort(key=lambda x: x.dedup_priority)
        merged_target = group_targets[0]
        for target in group_targets[1:]:
            if target.adb_serial is not None:
                merged_target.adb_serial = target.adb_serial
            merged_target.description = target.description
            merged_target.auto_connect_priority = max(merged_target.auto_connect_priority, target.auto_connect_priority)
            merged_target.override_identifier = target.override_identifier
            if target.preload_device_info:
                if merged_target.preload_device_info is None:
                    merged_target.preload_device_info = {}
                merged_target.preload_device_info.update(target.preload_device_info)
            merged_target.dedup_priority = target.dedup_priority
            merged_target.adb_server = target.adb_server
        deduped.append(merged_target)
    return deduped





