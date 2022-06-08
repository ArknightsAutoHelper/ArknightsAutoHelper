def enum_targets():
    import app
    result = []
    if app.config.device.extra_enumerators.bluestacks_hyperv:
        from .bluestacks_hyperv import enum as enum_bluestacks_hyperv, availiable as hyperv_enabled
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
