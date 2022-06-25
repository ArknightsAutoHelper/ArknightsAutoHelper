from typing import Optional
from automator.control.types import ControllerTarget

def enum_targets():
    import app
    result = []
    if app.config.device.extra_enumerators.bluestacks_hyperv:
        from .bluestacks_hyperv import enum as enum_bluestacks_hyperv
        result.extend(enum_bluestacks_hyperv())
    if app.config.device.extra_enumerators.vbox_emulators:
        from .vbox import enum as enum_vbox
        result.extend(enum_vbox())
    from .devices import enum as enum_adb
    result.extend(enum_adb())
    if app.config.device.extra_enumerators.append:
        from .append import enum as enum_append
        result.extend(enum_append())
    from ..target import dedup_targets
    return dedup_targets(result)

def get_target_from_adb_serial(serial, enumerated_targets: Optional[list[ControllerTarget]] = None):
    if enumerated_targets is None:
        enumerated_targets = enum_targets()
    from ..target import ADBControllerTarget
    for target in enumerated_targets:
        if isinstance(target, ADBControllerTarget) and target.adb_serial == serial:
            return target
    from ..client import get_config_adb_server
    server = get_config_adb_server()
    return ADBControllerTarget(server, serial, 'unknown adb target', None, 0, 0)
