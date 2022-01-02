def enum_devices():
    from .ADBConnector import ADBConnector, enum as adb_enum
    import config
    always_use_device = config.get('device/adb_always_use_device', None)
    if always_use_device is not None:
        return [(f'ADB: {always_use_device} (forced)', ADBConnector, [always_use_device], 'strong')]
    result = []
    adb_enum(result)
    import importlib
    extra_enumerators = config.get('device/extra_enumerators', {})
    for name in extra_enumerators:
        try:
            enumerator_module = importlib.import_module('.enumerator.' + name, __name__)
            enumerator_module.enum(result)
        except ImportError:
            pass
    return result

def auto_connect():
    devices = enum_devices()
    strong_devices = [x for x in devices if x[3] == 'strong']
    weak_devices = [x for x in devices if x[3] == 'weak']
    if len(strong_devices) == 1:
        _, cls, args, binding = strong_devices[0]
        return cls(*args)
    elif len(strong_devices) > 1:
        raise IndexError("more than one device connected")
    # len(strong_devices) == 0
    elif len(weak_devices) >= 1:
        import logging
        logger = logging.getLogger(__name__)
        for name, cls, args, binding in weak_devices:
            try:
                logger.info('trying device %s', name)
                connector = cls(*args)
                return connector
            except:
                pass
    else:  # len(strong_devices) == 0 and len(weak_devices) == 0
        raise IndexError("no device connected")
