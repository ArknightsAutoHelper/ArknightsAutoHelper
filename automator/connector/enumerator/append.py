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

def enum(devices):
    from ..ADBConnector import ADBConnector
    import app
    targets: list[str] = app.config.device.extra_enumerators.append
    if targets is None:
        return
    # check if target serial is already enumerated
    for display_name, connector_class, args, weight in devices:
        if connector_class is ADBConnector and weight == 'strong':
            for i, serial in enumerate(targets):
                if len(args) == 1 and compare_adb_serial(args[0], serial):
                    targets.pop(i)
    for target in targets:
        devices.append((f'ADB: {target} (append)', ADBConnector, [target], 'weak'))
