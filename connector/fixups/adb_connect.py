import logging

logger = logging.getLogger(__name__)


def run(connector, params):
    tryall = params.get('try_all', False)
    targets = params.get('target', None)
    if targets is None:
        return False
    if isinstance(targets, str):
        targets = [targets]
    result = False
    for target in targets:
        try:
            logger.info('尝试连接 %s', target)
            connector.paranoid_connect(target, timeout=0.5)
            result = True
            if not tryall:
                break
        except Exception as e:
            logger.warning("adb connect %r: %s", target, getattr(e, "message", repr(e)))
    return result
