# Arknghts Auto Helper
> 明日方舟辅助脚本，当然只是开发阶段

## 0x01 ADBShell 
基于夜神模拟器集成了多种adb操作方法，可以进行安卓辅助开发。当然你要在电脑端跑

### 运行须知

#### config 设置
**分辨率**

在config.config 下还有一个参数，为ADB_HOST 夜深模拟器第一个模拟器的HOST 是 127.0.0.1:62001
如果是其他模拟器，则需要修改。当然你也可以留空，系统会自动检测
由于该脚本没有做适配，仅仅测试了夜神模拟器，其他模拟器请自行测试。

另外，请确定夜神模拟器的分辨率是否调整为`1280*720`。由于作者精力有限，只做了绝对坐标的，欢迎大家重写模块
在运行过程中，请不要对模拟器进行缩放，以免造成不必要的麻烦


**非常重要的路径设置**
在config.py底下要改一个路径，如下所示

-  ADB_ROOT 
        这个路径为你 安卓模拟器adb工具的路径 （一般安卓电脑模拟器都有，所以设置成模拟器路径即可）
```python
ADB_ROOT = r"D:\Program Files\Nox\bin"
```

**OCR高级选项设置**
注意：以下选项如果要开启的话，请使用前确认已经安装 中文识别 或者 启动百度API

```
# 启动ocr来检测关卡后是否升级；默认方法为子图识别
enable_ocr_check_update = True
# 启动ocr来检测关卡是否结束；默认方法为子图识别
enable_ocr_check_end = True
# 启用ocr来DEBUG；默认方法为子图识别
enable_ocr_debugger = True
# 启用ocr输出，建议重定向到 Null。不然你的命令行输出会非常好看
enable_rebase_to_null = True

# 是否启用百度api作为ocr识别方案，需要自行注册，不启用则使用默认方案（OCR的方案）
Enable_api = False
""" 你的 APPID AK SK """
APP_ID = '你的 App ID'
API_KEY = '你的 Api Key'
SECRET_KEY = '你的 Secret Key'
```
**所有的设置可以在`config/default_setting.json`**下修改

#### 依赖包相关

一键安装所有依赖
```python
$ pip install -r requirement.txt
```

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
![TIM截图20190513101009.png-1013.8kB][1]


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

## 0x03 ArknightsHelper GUI
### GUI 启动

目前GUI功能还在测试中，会在之后的时日里日渐完善。现在的样子如下所示.

![TIM图片20190612102050.png-48.6kB][2]

启动方法很简单，执行 GUI_start.py即可

```python
from GUI import start_app
start_app()
```

### 未安装 OCR的初始理智设置方法

在初始化完毕，之后，设置当前理智值。请根据提示输入当前理智即可
⚠ 这个模块还没有充分测试，请既没有用百度OCR也没有自己装OCR的同学自己测试

### 的相关设置

在 `GUI/Settings/gui_settings.json`下包含了gui的设置。

- enable_init_ark_on_start ： 是否在启动 GUI 的时候同步启动 ark类。
    - 如果将该选项设置为 true 启动可能会有些短暂的延时

## 0x03 自定义开发与TODO

### 关于后续的想法

- [ ] 利用抓包获取升级等信息
- [ ] GUI 功能完善化
- [ ] config 文件设置 GUI化
- [ ] 更多的主线关卡支持
- [ ] 自动访问好友基建的支持
- [ ] 自动1-11支持【提issue的朋友我觉得你可以试试按键精灵】
- [ ] 坐标相对化

### 自定义开发与更多功能

详情请联系作者或者提出你的issue！祝大家玩的愉快

欢迎来加好友QQ 2454225341

也可以来加群
![qrcode_1558871927006.jpg-60.7kB][3]

在自定义开发之前，请把`config/__init__.py`改正为
```python
from config.shell_color import ShellColor, BufferColor
# 这行用的是python文件
from config.developer_config import *
# 备注:为了开发方便，应该将上面一行注释打开，不然你会看到你的编译器一片冒红
# 为此你需要同步 setting 文件的配置

# 这行用的是json文件
# from config.load_settings import *
from config.common_config import SCREEN_SHOOT_SAVE_PATH, STORAGE_PATH
```
把 `Arknights/click_location/__init__.py`改正为
```python
# 这行采用的是本地的python文件
from Arknights.click_location.click_location import *
# 这行采用的是本地的json文件
# from Arknights.click_location.load_click_locations import *

# 开发的时候请用Python文件
```
由于该版本是开发版本，所以所有的设置都写在python文件中方便调用。

另外，请对所有的类和函数在最外层进行调用。不然路径会出错


## 0x04 关于一些常见的问题

1. 分辨率/模拟器/路径问题
请看README
2. 我想跑一些别的关卡，但是提示我关卡不支持。
修改click_location中的LIZHI_CONSUME，添加你需要的关卡
你添加的关卡只能通过slim模式来启动
3. OCR 模块可以不装嚒？
可以不装，但是在使用脚本的时候请初始化理智值。目前而言，如果没有装OCR模块，你不能用GUI的版本。我之后会添加支持。
推荐安装GUI模块。因为这样能让一些地方的容错率变高。关于OCR的安装可以看文档。有人提议咱们可以用抓包来做。之后我会考虑这个功能，如果时间充裕的话（很显然是不充足的）
4. 我不会python|我电脑里没装Python，我能用这个嚒？
不能。我没有精力去给你整个exe文件。但是你也许可以通过我的代码学习一些Python的小技巧。
5. 之后会收费么？
不会，该项目一直开源。实际上作者还有别的事情要做，代码可能突然会有一段时间不更新了。


  [1]: http://static.zybuluo.com/shaobaobaoer/7ifp1acn3an7a3z23t96owt1/TIM%E6%88%AA%E5%9B%BE20190530114456.png
  [2]: http://static.zybuluo.com/shaobaobaoer/860t36w2ygsvet6sxn3lv3ty/TIM%E5%9B%BE%E7%89%8720190612102050.png
  [3]: http://static.zybuluo.com/shaobaobaoer/14ufv5gx72buoo1vyaa9jmgy/qrcode_1558871927006.jpg