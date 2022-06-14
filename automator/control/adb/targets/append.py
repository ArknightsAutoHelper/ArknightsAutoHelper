from automator.control.adb.client import get_config_adb_server
from automator.control.adb.target import ADBControllerTarget


def canonicalize_adb_serial(serial: str):
    """convert emulator-{X} to 127.0.0.1:{X+1}"""
    try:
        if serial.startswith('emulator-'):
            control_port = int(serial[9:])
            return f'127.0.0.1:{control_port+1}'
    except:
        pass
    return serial

def compare_adb_serial(a, b):
    a = canonicalize_adb_serial(a)
    b = canonicalize_adb_serial(b)
    return a == b

def enum():
    import app
    targets: list[str] = app.config.device.extra_enumerators.append
    if targets is None:
        return []
    # check if target serial is already enumerated
    server = get_config_adb_server()
    return [ADBControllerTarget(server, None, 'append', target, 0, 0) for target in targets]
