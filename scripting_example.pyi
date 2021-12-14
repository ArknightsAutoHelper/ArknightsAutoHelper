# 初始化 launcher
import Arknights.configure_launcher
# 使用 command 运行 CLI 界面中的命令
from automator.launcher import command

command('connect adb 127.0.0.1:7555')
command('auto -r 1-7 9999')

# 可以混合任何 Python 代码
import os
if os.environ.get('START_EMULATOR', None) is not None:
    os.system(r'"C:\Program Files\BlueStacks_bgp64_hyperv\HD-RunApp.exe" -json "{\"app_icon_url\":\"\",\"app_name\":\"arknights\",\"app_url\":\"\",\"app_pkg\":\"com.hypergryph.arknights\"}"')

# 默认在遇到错误时会抛出异常终止执行
command('auto -r NON_EXIST_STAGE 9999')  # 试图进入不存在的关卡，产生异常
command('record play get_credit')        # 由于异常更改了控制流不会被执行

# 可以使用 on_error_resume_next 禁用从 command() 抛出异常
from automator.launcher import on_error_resume_next
on_error_resume_next()

command('auto -r NON_EXIST_STAGE 9999')  # 试图进入不存在的关卡
command('record play get_credit')        # 继续执行
command('auto grass')

# 可以使用 on_error_raise_exception 恢复默认错误处理行为（抛出异常）
from automator.launcher import on_error_raise_exception
on_error_raise_exception()

command('auto -r NON_EXIST_STAGE 9999')  # 抛出异常

# 还可以直接调用面向对象的 API
from automator.launcher import helper
# 几乎所有的与游戏逻辑有关的功能都在 addon 内实现
helper.addon('StageNavigator').goto_stage('1-7')
# 或者将 addon 的类实例传给 addon() 以在 IDE 中获得成员提示
from Arknights.addons.combat import CombatAddon
helper.addon(CombatAddon).configure_refill(with_item=True, with_originium=False).combat_on_current_stage(1000)
# 查询所有的 addon
import pprint
pprint.pprint(helper.addons)

# 可以使用 import * 代替以上四个 from Arknights.launcher import
from automator.launcher import *  # command, helper, on_error_resume_next, on_error_raise_exception
