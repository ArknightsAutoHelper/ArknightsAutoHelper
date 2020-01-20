from .fancycli import fancywait


def skipcallback(handler):
    raise StopIteration

def delay_impl_factory(helper, statusline, show_toggle):
    togglelabel = lambda: '<r>切换自动补充理智(%s)' % ('ON' if helper.use_refill else 'OFF')

    def togglecallback(handler):
        helper.use_refill = not helper.use_refill
        handler.label = togglelabel()

    skiphandler = fancywait.KeyHandler('<ENTER>跳过', b'\r', skipcallback)
    skipdummy   = fancywait.KeyHandler('           ', b'', lambda x: None)
    if show_toggle and helper.use_refill:
        togglehandler = fancywait.KeyHandler(togglelabel(), b'r', togglecallback)
    else:
        togglehandler = fancywait.KeyHandler(None, None, None)

    def delay_impl(timeout):
        fancywait.fancy_delay(timeout, statusline, [skiphandler if timeout > 9 else skipdummy, togglehandler])

    return delay_impl

def _create_helper(show_toggle=False):
    from Arknights.base import ArknightsHelper
    helper = ArknightsHelper()

    io = sys.stdout.buffer
    if hasattr(io, 'raw'):
        io = io.raw
    line = fancywait.StatusLine(io)
    helper._shellng_with = line
    helper.delay_impl = delay_impl_factory(helper, line, show_toggle)
    return helper

def quick(argv):
    """
    quick [n]
        重复挑战当前画面关卡特定次数或直到理智不足
    """
    if len(argv) == 2:
        count = int(argv[1])
    else:
        count = 114514
    helper = _create_helper(True)
    with helper._shellng_with:
        helper.module_battle_slim(
            c_id=None,
            set_count=count,
        )
    return 0


class ItemsWrapper:
    def __init__(self, obj):
        self.obj = obj
    def __len__(self):
        return len(self.obj)
    def items(self):
        return self.obj

def auto(argv):
    """
    auto stage1 count1 [stage2 count2] ...
        按顺序挑战指定关卡特定次数直到理智不足
    """
    from Arknights.click_location import MAIN_TASK_SUPPORT
    arglist = argv[1:]
    if len(arglist) % 2 != 0:
        print('usage: auto stage1 count1 [stage2 count2] ...')
        return 1
    it = iter(arglist)
    tasks = [(stage, int(counts)) for stage, counts in zip(it, it)]
    for stage, count in tasks:
        if stage not in MAIN_TASK_SUPPORT:
            print('stage %s not supported' % stage)
            return 1
    helper = _create_helper(True)
    with helper._shellng_with:
        helper.main_handler(
            clear_tasks=True,
            task_list=ItemsWrapper(tasks)
        )
    return 0


def collect(argv):
    """
    collect
        收集每日任务奖励
    """
    helper = _create_helper()
    with helper._shellng_with:
        helper.clear_daily_task()
    return 0


def recruit(argv):
    """
    recruit
        公开招募识别
    """
    raise NotImplementedError()


def help(argv):
    """
    help
        输出本段消息
    """
    print("usage: %s command [command args]" % argv[0])
    print("commands:")
    for cmd in cmds:
        print("    " + str(cmd.__doc__.strip()))


cmds = [quick, auto, collect, recruit, help]


def main(argv):
    if len(argv) < 2:
        help(argv)
        return 1
    usecmd = argv[1]
    targetcmd = [x for x in cmds if x.__name__.startswith(usecmd)]
    if len(targetcmd) == 1:
        return targetcmd[0](argv[1:])
    elif len(targetcmd) == 0:
        print("unrecognized command: " + usecmd)
        help(argv)
        return 1
    else:
        print("ambiguous command: " + usecmd)
        print("matched commands: " + ','.join(x.__name__ for x in targetcmd))
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))

__all__ = ['main']
