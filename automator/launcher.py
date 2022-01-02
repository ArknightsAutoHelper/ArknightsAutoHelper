from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Union
    from automator import BaseAutomator
del TYPE_CHECKING
import os
import sys
import time

import config

from .fancycli import fancywait
from .fancycli.platform import isatty

config.enable_logging()

helper: BaseAutomator = None
prompt_prefix = 'akhelper'

def skipcallback(handler):
    raise StopIteration

class ShellNextFrontend:
    def __init__(self, use_status_line,):
        self.use_status_line = use_status_line
        if use_status_line:
            io = sys.stdout.buffer
            if hasattr(io, 'raw'):
                io = io.raw
            line = fancywait.StatusLine(io)
            self.statusline = line
    def attach(self, helper):
        self.helper = helper
    def alert(self, title, text, level='info', details=None):
        pass
    def notify(self, name, value):
        pass
    def delay(self, secs, allow_skip):
        if not self.use_status_line:
            time.sleep(secs)
            return
        skiphandler = fancywait.KeyHandler('<ENTER>跳过', b'\r', skipcallback)
        skipdummy   = fancywait.KeyHandler('           ', b'', lambda x: None)
        fancywait.fancy_delay(secs, self.statusline, [skiphandler if allow_skip else skipdummy])
    def request_device_connector(self):
        _ensure_device()
        return device

def _create_helper(cls, use_status_line=True):
    frontend = ShellNextFrontend(use_status_line)
    helper = cls(device_connector=device, frontend=frontend)
    if use_status_line:
        context = frontend.statusline
    else:
        from contextlib import nullcontext
        context = nullcontext()
    frontend.context = context
    return helper, context



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
        return _interactive_connect()
    if connector_type == 'adb':
        return _connect_adb(connector_args)
    else:
        print('unknown connector type:', connector_type)
    return 1


def _interactive_connect():
    from automator import connector
    global device
    try:
        device = connector.auto_connect()
    except IndexError:
        devices = connector.enum_devices()
        if len(devices) == 0:
            print("当前无设备连接")
            raise
        print("检测到多台设备")
        for i, (name, *cdr) in enumerate(devices):
            print("%2d. %s" % (i+1, name))
        num = 0
        while True:
            try:
                num = int(input("请输入序号选择设备: "))
                if not 1 <= num < len(devices)+1:
                    raise ValueError()
                break
            except ValueError:
                print("输入不合法，请重新输入")
        name, cls, args, binding = devices[num-1]
        device = cls(*args)


def _connect_adb(args):
    from automator.connector.ADBConnector import ADBConnector, ensure_adb_alive
    ensure_adb_alive()
    global device
    if len(args) >= 0:
        serial = args[0]
        device = ADBConnector(serial)
        return 0
    else:
        print('usage: connect adb <serial>')
        return 1


def _ensure_device():
    if device is None:
        connect(['connect'])
    device.ensure_alive()


def command_internal(argv: Union[str, list[str]]):
    if len(argv) == 0 or argv[0] == '?' or argv[0] == 'help':
        print(' '.join(x[0] for x in interactive_cmds))
        return 0
    cmd = match_cmd(argv[0], interactive_cmds)
    if cmd is not None:
        with _alarm_context_factory():
            try:
                errorlevel = cmd(argv)
            except (Exception, KeyboardInterrupt) as e:
                errorlevel = e
                import traceback
                traceback.print_exc()
        return errorlevel
    return 1

raise_on_error: bool = True


def command(cmd: Union[str, list[str]]):
    if isinstance(cmd, str):
        import shlex
        argv = shlex.split(cmd)
    else:
        argv = cmd
    errorlevel = command_internal(argv)
    if errorlevel != 0 and raise_on_error:
        raise RuntimeError(errorlevel)
    return errorlevel


def on_error_resume_next():
    global raise_on_error
    raise_on_error = False


def on_error_raise_exception():
    global raise_on_error
    raise_on_error = True


def interactive(argv):
    """
    interactive
        进入交互模式，减少按键次数（
    """
    on_error_resume_next()
    helpcmds(interactive_cmds)
    errorlevel = None
    try:
        # prefer conhost line editing over pyreadline on Windows
        if os.name != 'nt':
            import readline
    except ImportError:
        pass
    if instance_id := config.get_instance_id():
        title = f"{prompt_prefix}-{instance_id}"
    else:
        title = prompt_prefix
    while True:
        try:
            if device is None:
                prompt = f"{title}> "
            else:
                prompt = f"{title} {str(device)}> "
            try:
                cmdline = input(prompt)
            except KeyboardInterrupt:
                print('')
                continue
            except EOFError:
                print('')  # print newline on EOF
                break
            errorlevel = command(cmdline)
        except SystemExit as e:
            errorlevel = e.code
            break
    return errorlevel


def helpcmds(cmds):
    print("commands (prefix abbreviation accepted):")
    for cmd in cmds:
        if cmd[2]:
            print("    " + str(cmd[2].strip()))
        else:
            print("    " + cmd[0])


argv0 = 'placeholder'


def help(argv):
    """
    help
        输出本段消息
    """
    print("usage: %s command [command args]" % argv0)
    helpcmds(global_cmds)


def exit(argv):
    sys.exit()

helper_cmds = []
global_cmds = []
interactive_cmds = []

def match_cmd(first, avail_cmds):
    targetcmd = [x for x in avail_cmds if x[0].startswith(first)]
    if len(targetcmd) == 1:
        return targetcmd[0][1]
    elif len(targetcmd) == 0:
        print("unrecognized command: " + first)
        return None
    else:
        print("ambiguous command: " + first)
        print("matched commands: " + ','.join(x[0] for x in targetcmd))
        return None

def _configure(prompt, helper_class):
    global prompt_prefix, helper, context
    prompt_prefix = prompt
    helper, context = _create_helper(helper_class)
    global_cmds.extend([*helper._cli_commands.values(), ('interactive', interactive, interactive.__doc__), ('help', help, help.__doc__)])
    interactive_cmds.extend([('connect', connect, connect.__doc__), *helper._cli_commands.values(), ('exit', exit, '')])


def main(argv):
    if helper is None:
        raise ValueError('launcher not configured')
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


__all__ = ['helper', 'command', 'on_error_resume_next', 'on_error_raise_exception']

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))

