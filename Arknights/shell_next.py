import itertools
import sys
import time

from .fancycli import fancywait
from .fancycli.platform import isatty


def skipcallback(handler):
    raise StopIteration


def delay_impl_factory(helper, statusline, show_toggle):
    togglelabel = lambda: '<r>切换自动补充理智(%s)' % ('ON' if helper.use_refill else 'OFF')

    def togglecallback(handler):
        helper.use_refill = not helper.use_refill
        handler.label = togglelabel()

    skiphandler = fancywait.KeyHandler('<ENTER>跳过', b'\r', skipcallback)
    skipdummy   = fancywait.KeyHandler('           ', b'', lambda x: None)
    if not helper.refill_with_item and not helper.refill_with_originium:
        show_toggle = False
    if show_toggle and helper.use_refill:
        togglehandler = lambda: fancywait.KeyHandler(togglelabel(), b'r', togglecallback)
    else:
        togglehandler = lambda: fancywait.KeyHandler(None, None, None)

    def delay_impl(timeout):
        fancywait.fancy_delay(timeout, statusline, [skiphandler if timeout > 9 else skipdummy, togglehandler()])

    return delay_impl


def _create_helper(show_toggle=False):
    from Arknights.helper import ArknightsHelper
    helper = ArknightsHelper()

    io = sys.stdout.buffer
    if hasattr(io, 'raw'):
        io = io.raw
    line = fancywait.StatusLine(io)
    helper._shellng_with = line
    helper.delay_impl = delay_impl_factory(helper, line, show_toggle)
    return helper

def _parse_opt(argv):
    ops = []
    if len(argv) >= 2 and argv[1][:1] in ('+', '-'):
        opts = argv.pop(1)
        action = None
        for c in opts:
            if c == '+':
                action = True
            elif c == '-':
                action = False
            elif c == 'r':
                if action is not None:
                    def op(helper):
                        helper.use_refill = action
                        helper.refill_with_item = action
                    ops.append(op)
            elif c == 'R':
                if action is not None:
                    def op(helper):
                        helper.refill_with_originium = action
                    ops.append(op)
    return ops


class AlarmContext:
    def __init__(self, duration=60):
        self.duration = duration

    def __enter__(self):
        self.t0 = time.monotonic()

    def __exit__(self, exc_type, exc_val, exc_tb):
        t1 = time.monotonic()
        if t1 - self.t0 >= self.duration:
            self.alarm()

    def alarm(self):
        pass


class BellAlarmContext(AlarmContext):
    def alarm(self):
        print('\a', end='')


def _alarm_context_factory():
    if isatty(sys.stdout):
        return BellAlarmContext()
    return AlarmContext()


def quick(argv):
    """
    quick [+-rR] [n]
        重复挑战当前画面关卡特定次数或直到理智不足
        +r/-r 是否自动回复理智
        +R/-R 是否使用源石回复理智（需要同时开启 +r）
    """

    ops = _parse_opt(argv)
    if len(argv) == 2:
        count = int(argv[1])
    else:
        count = 114514
    helper = _create_helper(True)
    for op in ops:
        op(helper)
    with helper._shellng_with:
        helper.module_battle_slim(
            c_id=None,
            set_count=count,
        )
    return 0


def auto(argv):
    """
    auto [+-rR] stage1 count1 [stage2 count2] ...
        按顺序挑战指定关卡特定次数直到理智不足
    """
    ops = _parse_opt(argv)
    arglist = argv[1:]
    if len(arglist) % 2 != 0:
        print('usage: auto [+-rR] stage1 count1 [stage2 count2] ...')
        return 1
    it = iter(arglist)
    tasks = [(stage.upper(), int(counts)) for stage, counts in zip(it, it)]

    helper = _create_helper(True)
    for op in ops:
        op(helper)
    with helper._shellng_with:
        helper.main_handler(
            clear_tasks=False,
            task_list=tasks,
            auto_close=False
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
    recruit [tags ...]
        公开招募识别/计算，不指定标签则从截图中识别
    """
    from . import recruit_calc

    if 2 <= len(argv) <= 6:
        tags = argv[1:]
        result = recruit_calc.calculate(tags)
    elif len(argv) == 1:
        helper = _create_helper()
        with helper._shellng_with:
            result = helper.recruit()
    else:
        print('要素过多')
        return 1

    colors = ['\033[36m', '\033[90m', '\033[37m', '\033[32m', '\033[93m', '\033[91m']
    reset = '\033[39m'
    for tags, operators, rank in result:
        taglist = ','.join(tags)
        if rank >= 1:
            taglist = '\033[96m' + taglist + '\033[39m'
        print("%s: %s" % (taglist, ' '.join(colors[op[1]] + op[0] + reset for op in operators)))


def interactive(argv):
    """
    interactive
        进入交互模式，减少按键次数（
    """
    import shlex
    import traceback
    helpcmds(interactive_cmds)
    errorlevel = None
    while True:
        try:
            cmdline = input("akhelper> ")
            argv = shlex.split(cmdline)
            if len(argv) == 0 or argv[0] == '?' or argv[0] == 'help':
                print(' '.join(x.__name__ for x in interactive_cmds))
                continue
            elif argv[0] == 'exit':
                break
            cmd = match_cmd(argv[0], interactive_cmds)
            if cmd is not None:
                with _alarm_context_factory():
                    errorlevel = cmd(argv)
        except EOFError:
            print('')  # print newline on EOF
            break
        except (Exception, KeyboardInterrupt) as e:
            errorlevel = e
            traceback.print_exc()
            continue
    return errorlevel


argv0 = 'placeholder'


def helpcmds(cmds):
    print("commands (prefix abbreviation accepted):")
    for cmd in cmds:
        if cmd.__doc__:
            print("    " + str(cmd.__doc__.strip()))
        else:
            print("    " + cmd.__name__)


def help(argv):
    """
    help
        输出本段消息
    """
    print("usage: %s command [command args]" % argv0)
    helpcmds(global_cmds)


def exit(argv):
    sys.exit()


global_cmds = [quick, auto, collect, recruit, interactive, help]
interactive_cmds = [quick, auto, collect, recruit, exit]

def match_cmd(first, avail_cmds):
    targetcmd = [x for x in avail_cmds if x.__name__.startswith(first)]
    if len(targetcmd) == 1:
        return targetcmd[0]
    elif len(targetcmd) == 0:
        print("unrecognized command: " + first)
        return None
    else:
        print("ambiguous command: " + first)
        print("matched commands: " + ','.join(x.__name__ for x in targetcmd))
        return None

def main(argv):
    global argv0
    argv0 = argv[0]
    if len(argv) < 2:
        interactive(argv[1:])
        return 1
    targetcmd = match_cmd(argv[1], global_cmds)
    if targetcmd is not None:
        return targetcmd(argv[1:])
    else:
        help(argv)
    return 1


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))

__all__ = ['main']
