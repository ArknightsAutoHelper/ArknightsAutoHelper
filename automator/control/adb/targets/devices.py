from automator.control.adb.target import ADBControllerTarget


def serial_to_address(serial: str):
    """convert emulator-{X} to 127.0.0.1:{X+1}"""
    try:
        if serial.startswith('emulator-'):
            control_port = int(serial[9:])
            return f'127.0.0.1:{control_port+1}'
    except:
        pass
    return serial

def enum():
    from automator.control.adb.client import get_config_adb_server
    server = get_config_adb_server()
    devices = [x[0] for x in server.devices()]
    return [ADBControllerTarget(server, target, f'adb connected', serial_to_address(target), 1, 1) for target in devices]