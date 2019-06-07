# Arknghts Auto Helper
> 明日方舟辅助脚本，当然只是开发阶段

## 0x01 ADBShell 
基于夜神模拟器集成了多种adb操作方法，可以进行安卓辅助开发。当然你要在电脑端跑

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

如想要二次开发，请修改`config.py`下的相关参数。以绝对路径为佳。

关于修改方法和样例代码，可以参考`ArknightsHelper_examples.py`下的代码和说明


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
urllib3    1.24.2
baidu-aip  2.2.13.0
```

### 目前支持的功能

 - ADB 指令
 - 点击动作
 - 拖动动作
 - 截图动作
 - 获取子图
 - 子图与目标子图比较
 - OCR 检测识别
 - 百度OCR （感谢群友的贡献，目前该功能基本完善，如有BUG请多多包涵）

## 0x02 ArknightsHelper
> 需要安装OCR模块;感谢群友的贡献！

### 快速启动！快乐护肝！

之后通过这样的代码就可以迅速开始战斗，你需要手动选关。到如下画面，活动关卡你也可以这么刷

```python
from Arknights import ArknightsHelper
Ark = ArknightsHelper()
Ark.module_battle_slim(c_id='4-8', set_count=8)
# c_id 是战斗章节
# set_count 是战斗次数
```
![TIM截图20190513101009.png-1013.8kB][4]


理论上该模块比完整的模块稳定并且不容易被系统检测。并且该模块所有的点击序列都是随机化的，不容易被检测

### 多开启动！效率至上！
关于多开器的用法
请在初始化前，带入 ADB_HOST。如果你不知道你的 ADB_HOST 是多少，就带入一个空值。系统会自动检测,并让你手动选择。

    [!] 检测到多台设备，根据 ADB_HOST 参数将自动选择设备
    [*]  0	127.0.0.1:62025	device
    [*]  1	127.0.0.1:62001	device
    系统未检测到设备名称，请根据上述内容自行输入数字并选择
    >0
    127.0.0.1:62025

请不要直接带入和你另一个设备同样的ADB_HOST，这样会导致连到另一台设备上去

```python
from Arknights import ArknightsHelper
ADB_HOST = "127.0.0.1:62025"
# OR ADB_HOST = ""
Ark = ArknightsHelper(adb_host=ADB_HOST)
Ark.module_battle_slim(c_id='CE-3', set_count=50, set_ai=True)
```

### 任务清单功能

通过传入任务清单可以执行一系列任务。
目前支持的关卡请看在click_location.LIZHI_CONSUME中的关卡章节。
基本上里面的所有章节都测试过，但是总有一些奇奇怪怪的状况发生。并且请不要让你的自律翻车。不然就没了

```python
from Arknights import ArknightsHelper
from collections import OrderedDict

TASK_LIST = OrderedDict()
TASK_LIST['LS-4'] = 10
Ark = ArknightsHelper()
Ark.main_handler(TASK_LIST)
```

### 未安装OCR模块的用法
> ⚠ 由于脚本逐渐完善化以及日趋增加的错误处理能力。在之后的版本中将会逐渐废弃未安装OCR模块的支持。
为此希望能够自行安装OCR模块或者调用百度API来识别。关于OCR的安装可以看 OCR_install.md

如果你没有安装OCR模块，需要在初始化时候赋予初值，该值为你当前的理智。
由于系统不知道你啥时候升级，所以减好了还需要重新设置。

```python
from Arknights import ArknightsHelper
from collections import OrderedDict

TASK_LIST = OrderedDict()
TASK_LIST['LS-4'] = 10
Ark = ArknightsHelper(100)# 
Ark.main_handler(TASK_LIST)
```

### 启动百度API的方式识别OCR
#### 百度普通的文字识别免费为50000次/日，可以开通付费，超过免费调用量后，按次计费
文档地址：https://cloud.baidu.com/doc/OCR/index.html
需要安装 ```baidu-aip```库，执行```pip install baidu-aip```即可
启用百度api作为ocr识别方案，需要自行注册百度云
```False```则使用默认的原始方案
```
Enable_api = False
```

### OCR检测关卡的方法

#### 相关配置文件在config.py下

启动ocr来检测关卡后是否升级
注意：如不使用百度api并要使用ocr识别的话，请使用前确认已经安装中文识别
```
enable_ocr_check_update = False
```
启动ocr来检测关卡是否结束
```
enable_ocr_check_end = False
```
默认方法为利用子图识别


### 关于后续的想法

目前所有功能基本完善了，我也用的比较爽了。总之刷材料啥的都没啥问题。

之后可能会用 WXPYTHON 写个GUI。另外会写个访问好友基建的脚本。

### 自定义开发与更多功能

详情请联系作者或者提出你的issue！祝大家玩的愉快

欢迎来加好友QQ 2454225341

也可以来加群
![qrcode_1558871927006.jpg-60.7kB][6]


## 0x03 关于一些常见的问题




  [4]: http://static.zybuluo.com/shaobaobaoer/7ifp1acn3an7a3z23t96owt1/TIM%E6%88%AA%E5%9B%BE20190530114456.png  
  [6]: http://static.zybuluo.com/shaobaobaoer/14ufv5gx72buoo1vyaa9jmgy/qrcode_1558871927006.jpg
