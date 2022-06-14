from .types import ControllerTarget

def enum_targets() -> list[ControllerTarget]:
    from .adb.targets import enum_targets
    return enum_targets()

def _is_valid_ip_port(ip_port: str):
    import ipaddress
    import re
    try:
        match = re.match(r'^(\d+\.\d+\.\d+\.\d+):(\d+)$', ip_port)
        if match:
            ip = ipaddress.ip_address(match.group(1))
            port = int(match.group(2))
            return 1 <= port <= 65535
    except:
        return False

def get_auto_connect_candidates(targets: list[ControllerTarget] = ..., preference: str = None) -> list[ControllerTarget]:
    """
    Returns target with highest auto_connect_priority.

    If more than one target returned, caller should try each target until connected.
    """
    if targets is ...:
        targets = enum_targets()
    if not targets:
        return []
    if preference is not None:
        from .adb.target import ADBControllerTarget
        # preference can be:
        #   - target identifier (hyperv:bstk:Nougat64_nxt)
        #   - adb serial (emulator-5554)
        #   - adb address (127.0.0.1:5555)
        for target in targets:
            if target.describe()[0] == preference:
                return [target]
            if isinstance(target, ADBControllerTarget):
                if target.adb_serial == preference:
                    return [target]
                if target.adb_address == preference:
                    return [target]
        if _is_valid_ip_port(preference):
            from .adb.client import get_config_adb_server
            return [get_config_adb_server().get_device(preference)]
        raise IndexError(f'preference {preference} not found')
    max_priority = max(x.auto_connect_priority for x in targets)
    max_tier_targets = [x for x in targets if x.auto_connect_priority == max_priority]
    if max_priority > 0:
        if len(max_tier_targets) == 1:
            return [max_tier_targets[0]]
        elif len(max_tier_targets) > 1:
            raise IndexError(f'Multiple targets enumerated with auto connect priority {max_priority}')
        else:
            return []
    else:
        return max_tier_targets

def auto_connect(targets: list[ControllerTarget] = ..., preference: str = None):
    selected_targets = get_auto_connect_candidates(targets)
    if len(selected_targets) == 0:
        raise IndexError("no target enumerated")
    if len(selected_targets) == 1:
        return selected_targets[0].create_controller()
    
    import logging
    logger = logging.getLogger(__name__)
    for target in selected_targets:
        try:
            logger.info('trying target %s', target)
            control = target.create_controller()
            return control
        except:
            pass
    raise IndexError('No target enumerated')

def _test():
    import logging
    logging.basicConfig(level=logging.DEBUG, force=True)
    import app
    app.init()
    targets = enum_targets()
    print('====== enunmerated targets ======')
    for target in targets:
        print(target)

if __name__ == '__main__':
    _test()
