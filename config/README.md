# CONFIG 说明文档
> 由于辅助的日益完善，和开发者贡献的代码逐渐丰富。决定将设置相关的内容放到此处，供大家编写。

## 0x00 基础设置相关

**ADB_ROOT**

 - adb.exe 的所在路径。最后不需要加斜杠。可以自行配置。
 - 目前将 adb.exe 直接包进来，也许根本上解决ADB_ROOT需要手动配置的问题;考虑到adb.exe比较大之后可能采用扩展包的形式

**ADB_HOST**

 - 设备对应的名称。系统会用 `adb devices`自动检测ADB_HOST是否激活。

**enable_adb_host_auto_detect**

 - 可以开启如下选项，跳过ADB_HOST的自动检测环节
 - 对于MUMU模拟器等无法用 adb devices 命令 读取到端口的模拟器
 - 设置为 False 必须保证 ADB_HOST 已经正确填写；如果不需要使用多开器，也可以开启如下选项，能够让你启动更快


### 关于多开器的用法
如果想用多开器，请将 enable_adb_host_auto_detect 设置为 True。如果系统检测成功会出现如下命令行

    [!] 检测到多台设备，根据 ADB_HOST 参数将自动选择设备
    [*]  0	127.0.0.1:62025	device
    [*]  1	127.0.0.1:62001	device
    系统未检测到设备名称，请根据上述内容自行输入数字并选择
    >0
    127.0.0.1:62025

自行选择设备即可。

## 0x01 OCR 基础设置相关
注意：以下选项如果要开启的话，请使用前确认已经安装 中文识别 或者 启动百度API

```python
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
```

## 0x02 百度 OCR 设置相关

```python
# 是否启用百度api作为ocr识别方案，需要自行注册，不启用则使用默认方案
enable_baidu_api = False
# 是否对使用百度ocr的图像进行处理，有可能改善精准度，但也有可能反而导致识别错误；该选项不会影响tesseract
enable_help_baidu = True
""" 你的 APPID AK SK """
APP_ID = '你的 App ID'
API_KEY = '你的 Api Key'
SECRET_KEY = '你的 Secret Key'
```
## 0x03 其他设置

```python
# 是否启动时打印一些系统变量方便DEBUG
# 0 为不输出 1 为输出函数调用 2 为输出全部调试信息
DEBUG_LEVEL = 2
# arknights 应用的相关配置
ArkNights_PACKAGE_NAME = "com.hypergryph.arknights"  # 这个是官服的设置
# ArkNights_PACKAGE_NAME = "com.hypergryph.arknights.bilibili" # 这是b服的设置
ArkNights_ACTIVITY_NAME = "com.u8.sdk.U8UnityContext"
```