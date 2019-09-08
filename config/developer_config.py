"""
如果需要二次开发，请修改

    [⚠] 这个路径很重要 ADB_ROOT
            这个路径为你 安卓模拟器adb工具的路径 （一般安卓电脑模拟器都有，所以设置成模拟器路径即可）
    [⚠] 这个路径很重要 STORAGE_PATH
            也就是目录底下的 storage 文件夹，请确保是绝对路径
    [⚠] 这个路径重要 SCREEN_SHOOT_SAVE_PATH
            也就是目录底下的 screen_shoot 文件夹，用来存放一些截图
"""
ADB_ROOT = r"F:\Nox\bin"
# ADB_HOST = "127.0.0.1:62001"  # 如果你不想用多开器的功能，请用此行配置
ADB_HOST = ""  # 如果你想用多开器的功能，请使用此行配置，并手动选择或在启动时自行添加HOST。
# 另外推荐将这里的ADB_HOST 赋值为空字符串，如果仅有一台设备连接，系统会自动读取到设备名称
# 目前多开设备可能存在读写问题。后期会调整路径设置。

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
# 启用ocr输出
enable_rebase_to_null = True
# 是否启用百度api作为ocr识别方案，需要自行注册，不启用则使用默认方案
enable_baidu_api = False
# 是否对使用百度ocr的图像进行处理，有可能改善精准度，但也有可能反而导致识别错误；该选项不会影响tesseract
enable_help_baidu = True
""" 你的 APPID AK SK """
APP_ID = '你的 App ID'
API_KEY = '你的 Api Key'
SECRET_KEY = '你的 Secret Key'
# 是否启动时打印一些系统变量方便DEBUG
# 0 为不输出 1 为输出函数调用 2 为输出全部调试信息
DEBUG_LEVEL = 2

# arknights INFO
ArkNights_PACKAGE_NAME = "com.hypergryph.arknights"  # 这个是官服的设置
# ArkNights_PACKAGE_NAME = "com.hypergryph.arknights.bilibili" # 这是b服的设置
ArkNights_ACTIVITY_NAME = "com.u8.sdk.U8UnityContext"

# 之后请把内容固化到json文件,该文件只用于开发版本
