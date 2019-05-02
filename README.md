# shaobao_adb
> 明日方舟辅助脚本，当然只是开发阶段，只是刚刚上线我就很气！

## ADBShell 
基于夜神模拟器集成了多种安卓模拟器操作方法，可以进行安卓辅助开发。当然你要在电脑端跑

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

<!--行了行了...抽卡各种保底。心态崩了
看着别人在群里晒能天使我也很酸啊
然而我仓库里一群菜刀队不说...6*的到现在只抽到一个（5-2更新）
好的我懂了，就是老天让我好好学习不要整天打手游。反正本人手残塔防也玩不来。
不要说了，我把外挂开源了。我感觉我和这游戏缘分不咋地。记得添加点坐标，再`click_location.py`底下
当然想拿去二次开发或者自己用的话也可以。我感觉我和这游戏没缘分但也许未来还会说真香-->

