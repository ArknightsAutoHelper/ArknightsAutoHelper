import itertools
import sys
import time
import signal

from .fancycli import fancywait
from .fancycli.platform import isatty


def skipcallback(handler):
    raise StopIteration

class ShellNextFrontend:
    def __init__(self, use_status_line, show_toggle):
        self.show_toggle = show_toggle
        self.use_status_line = use_status_line
        if use_status_line:
            io = sys.stdout.buffer
            if hasattr(io, 'raw'):
                io = io.raw
            line = fancywait.StatusLine(io)
            self.statusline = line
    def attach(self, helper):
        self.helper = helper
    def notify(self, name, value):
        pass
    def delay(self, secs, allow_skip):
        if not self.use_status_line:
            time.sleep(secs)
            return
        if self.show_toggle:
            togglelabel = lambda: '<r>切换自动补充理智(%s)' % ('ON' if self.helper.use_refill else 'OFF')
            def togglecallback(handler):
                self.helper.use_refill = not self.helper.use_refill
                handler.label = togglelabel()
            togglehandler = lambda: fancywait.KeyHandler(togglelabel(), b'r', togglecallback)
        else:
            togglehandler = lambda: fancywait.KeyHandler(None, None, None)
        skiphandler = fancywait.KeyHandler('<ENTER>跳过', b'\r', skipcallback)
        skipdummy   = fancywait.KeyHandler('           ', b'', lambda x: None)
        fancywait.fancy_delay(secs, self.statusline, [skiphandler if allow_skip else skipdummy, togglehandler()])


def _create_helper(use_status_line=True, show_toggle=False):
    from Arknights.helper import ArknightsHelper
    _ensure_device()
    frontend = ShellNextFrontend(use_status_line, show_toggle)
    helper = ArknightsHelper(device_connector=device, frontend=frontend)
    if use_status_line:
        context = frontend.statusline
    else:
        from contextlib import nullcontext
        context = nullcontext()
    return helper, context

def _parse_opt(argv):
    ops = []
    if len(argv) >= 2 and argv[1][:1] in ('+', '-'):
        opts = argv.pop(1)
        enable_refill = None
        for i, c in enumerate(opts):
            if c == '+':
                enable_refill = True
            elif c == '-':
                enable_refill = False
            elif c == 'r' and enable_refill is not None:
                def op(helper):
                    helper.use_refill = enable_refill
                    helper.refill_with_item = enable_refill
                ops.append(op)
            elif c == 'R' and enable_refill is not None:
                def op(helper):
                    helper.refill_with_originium = enable_refill
                ops.append(op)
            elif c in '0123456789' and enable_refill:
                num = int(opts[i:])
                def op(helper):
                    helper.max_refill_count = num
                ops.append(op)
                break
            else:
                raise ValueError('unrecognized token: %r in option %r' % (c, opts))
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


device = None


def connect(argv):
    """
    connect [connector type] [connector args ...]
        连接到设备
        支持的设备类型：
        connect adb [serial or tcpip endpoint]
    """
    connector_type = 'adb'
    if len(argv) > 1:
        connector_type = argv[1]
        connector_args = argv[2:]
    else:
        connector_args = []
    if connector_type == 'adb':
        _connect_adb(connector_args)
    else:
        print('unknown connector type:', connector_type)


def _connect_adb(args):
    from connector.ADBConnector import ADBConnector, ensure_adb_alive
    ensure_adb_alive()
    global device
    if len(args) == 0:
        try:
            device = ADBConnector.auto_connect()
        except IndexError:
            print("检测到多台设备")
            devices = ADBConnector.available_devices()
            for i, (serial, status) in enumerate(devices):
                print("%2d. %s\t[%s]" % (i, serial, status))
            num = 0
            while True:
                try:
                    num = int(input("请输入序号选择设备: "))
                    if not 0 <= num < len(devices):
                        raise ValueError()
                    break
                except ValueError:
                    print("输入不合法，请重新输入")
            device_name = devices[num][0]
            device = ADBConnector(device_name)
    else:
        serial = args[0]
        try:
            device = ADBConnector(serial)
        except RuntimeError as e:
            if e.args and isinstance(e.args[0], bytes) and b'not found' in e.args[0]:
                if ':' in serial and serial.split(':')[-1].isdigit():
                    print('adb connect', serial)
                    ADBConnector.paranoid_connect(serial)
                    device = ADBConnector(serial)
                    return
            raise


def _ensure_device():
    if device is None:
        connect(['connect'])
    device.ensure_alive()

def quick(argv):
    """
    quick [+-rR[N]] [n]
        重复挑战当前画面关卡特定次数或直到理智不足
        +r/-r 是否自动回复理智，最多回复 N 次
        +R/-R 是否使用源石回复理智（需要同时开启 +r）
    """

    ops = _parse_opt(argv)
    if len(argv) == 2:
        count = int(argv[1])
    else:
        count = 114514
    helper, context = _create_helper(show_toggle=True)
    for op in ops:
        op(helper)
    with context:
        helper.module_battle_slim(
            c_id=None,
            set_count=count,
        )
    return 0


def auto(argv):
    """
    auto [+-rR[N]] stage1 count1 [stage2 count2] ...
        按顺序挑战指定关卡特定次数直到理智不足
    """
    ops = _parse_opt(argv)
    arglist = argv[1:]
    if len(arglist) % 2 != 0:
        print('usage: auto [+-rR] stage1 count1 [stage2 count2] ...')
        return 1
    it = iter(arglist)
    tasks = [(stage.upper(), int(counts)) for stage, counts in zip(it, it)]

    helper, context = _create_helper(show_toggle=True)
    for op in ops:
        op(helper)
    with context:
        helper.main_handler(
            clear_tasks=False,
            task_list=tasks,
            auto_close=False
        )
    return 0


def collect(argv):
    """
    collect
        收集每日任务和每周任务奖励
    """
    helper, context = _create_helper()
    with context:
        helper.clear_task()
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
        helper, context = _create_helper(use_status_line=False)
        with context:
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
    try:
        import readline
    except ImportError:
        pass
    while True:
        try:
            if device is None:
                prompt = "akhelper> "
            else:
                prompt = "akhelper %s> " % str(device)
            cmdline = input(prompt)
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
interactive_cmds = [connect, quick, auto, collect, recruit, exit]

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
