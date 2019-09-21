import os
import sys


# 把 adb.exe 直接包进来，从根本上解决ADB_ROOT需要手动配置的问题;考虑到adb.exe比较大之后可能采用扩展包的形式
# 【如果谁可以贡献一个服务器的话;群主的学生机可能下的很慢.】
ADB_ROOT = os.path.abspath('./ADB/{platform}'.format(platform=sys.platform))
ADB_HOST = "127.0.0.1:60001"
ADB_SERVER = ('127.0.0.1', 5037)
# ADB_SERVER_MUMU = ('127.0.0.1', 114514)
# 对于MUMU模拟器等无法用 adb devices 命令 读取到端口的模拟器，可以开启如下选项，跳过ADB_HOST的自动检测环节
# 但是必须保证 ADB_HOST 已经正确填写；如果不需要使用多开器，也可以开启如下选项，能够让你启动更快
enable_adb_host_auto_detect = True

# 注意：以下选项如果要开启的话，请使用前确认已经安装 中文识别 或者 启动百度API
# 启动ocr来检测关卡后是否升级
enable_ocr_check_update = True
# 启动ocr来检测关卡是否结束
enable_ocr_check_end = True
# 启动ocr来检测任务是否已完成
enable_ocr_check_task = True
# 启用ocr来DEBUG
enable_ocr_debugger = True
# 启用ocr来检测是否在关卡界面
enable_ocr_check_is_TASK_page = True
# 禁用OCR输出;建议开启，不然你的命令行会非常精彩
enable_rebase_to_null = True

# 选择OCR引擎，非必要，设置为None则使用默认优先循序为1.tesseract, 2.windows_media_ocr 3.baidu
engine = None

# 是否启用百度api作为ocr识别方案之一，需要自行注册，不启用则使用默认方案，但在engine指定baidu的话该设置无效
enable_baidu_api = False
""" 你的 APPID AK SK """
APP_ID = '你的 App ID'
API_KEY = '你的 Api Key'
SECRET_KEY = '你的 Secret Key'
# 是否启动时打印一些系统变量方便DEBUG
# 0 为不输出 1 为输出函数调用 2 为输出全部调试信息
DEBUG_LEVEL = 2

# arknights 应用的相关配置
ArkNights_PACKAGE_NAME = "com.hypergryph.arknights"  # 这个是官服的设置
# ArkNights_PACKAGE_NAME = "com.hypergryph.arknights.bilibili" # 这是b服的设置
ArkNights_ACTIVITY_NAME = "com.u8.sdk.U8UnityContext"

# 之后请把内容固化到json文件,该文件只用于开发版本
