# shaobao_adb

## ADBShell 
基于夜神模拟器集成了多种安卓模拟器操作方法，可以进行安卓辅助开发。当然你要在电脑端跑

该分支主要用于更新ADBShell的额外功能。

### 运行须知

#### config.py
```python
ADB_ROOT = r"D:\Program Files\Nox\bin"
ADB_HOST = "127.0.0.1:62001"
SCREEN_SHOOT_SAVE_PATH = "D:\\python_box\\shaobao_adb\\screen_shoot\\"
STORAGE_PATH = "D:\\python_box\\shaobao_adb\\storage\\"

# arknights INFO
ArkNights_PACKAGE_NAME = "com.hypergryph.arknights"
ArkNights_ACTIVITY_NAME = "com.u8.sdk.U8UnityContext"
```

如想要二次开发，请修改`config.py`下的相关参数。以绝对路径为佳

#### 依赖包


```python
# python 版本 3.6 + 
Package    Version
---------- --------
certifi    2019.3.9
chardet    3.0.4
idna       2.8
Pillow     6.0.0
pip        10.0.1
requests   2.21.0
setuptools 39.1.0
soupsieve  1.9.1
tesserocr  2.4.0
urllib3    1.24.2
```

### 目前支持的功能

 - ADB 指令
 - 点击动作
 - 拖动动作
 - 截图动作
 - 获取子图
 - 子图与目标子图比较
