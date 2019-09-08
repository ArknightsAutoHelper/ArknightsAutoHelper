# Arknghts Auto Helper
明日方舟辅助脚本，分支说明如下

| 分支    | 说明    |
|:----|:----|
| master |目前的稳定版本|
|release |目前可以应用的GUI版本|
| dev |目前的开发版本|
| shaobao_adb |经过封装可以移植的ADB方法类|

## 0x01 设置相关 

### 分辨率要求
请确保夜神模拟器的分辨率已经调整为 `1280*720`。由于作者精力有限，暂时只做了绝对坐标，欢迎大家重写模块。
在运行过程中，请不要对模拟器进行缩放，以免造成不必要的麻烦。

### Config 文件设置
#### ☆非常重要的路径设置☆

在 `config\developer_config.py` 内要修改 `ADB_ROOT` 参数路径，这个路径为你所安装的安卓模拟器 adb 工具的路径 （一般安卓电脑模拟器都有，所以设置成模拟器路径即可）
```python
ADB_ROOT = r"D:\Program Files\Nox\bin"
```
需要注意的是，在该文件内还有一个参数，为 `ADB_HOST`（夜神模拟器第一个模拟器的 HOST 是`127.0.0.1:62001`）。
```python
ADB_HOST = "127.0.0.1:62001"
```
如果是其他模拟器，则需要修改。当然你也可以**留空**，系统会自动检测。
由于该脚本没有做适配，仅仅测试了夜神模拟器，其他模拟器请自行测试。

#### OCR 高级选项设置
**注意：**以下选项如果要开启的话，请使用前确认已经安装 中文识别 或者 启动百度API

```python
# 启动ocr来检测关卡后是否升级；默认方法为子图识别
enable_ocr_check_update = True
# 启动ocr来检测关卡是否结束；默认方法为子图识别
enable_ocr_check_end = True
# 启用ocr来DEBUG；默认方法为子图识别
enable_ocr_debugger = True
# 启用ocr来检测是否在关卡界面
enable_ocr_check_is_TASK_page = True
# 启用ocr输出，建议重定向到 Null。不然你的命令行输出会非常好看
enable_rebase_to_null = True
```

#### 启动百度API的方式识别 OCR
**百度普通的文字识别免费为50000次/日，可以开通付费，超过免费调用量后，按次计费**

文档地址：https://cloud.baidu.com/doc/OCR/index.html
需要安装 ```baidu-api```库，执行```pip install baidu-aip```即可（也包含于 `requirement.txt`）。
启用百度api作为ocr识别方案，需要自行注册百度云
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

### 依赖包相关

一键安装所有依赖
```python
$ pip install -r requirement.txt
```

### 日志说明

日志采用```import logging```在主目录下生成**ArknightsAutoHelper.log**，推荐用Excel打开，分割符号为“!”。

相关配置文件在```config```目录下的**logging.ini**，由于过于复杂 ~~其实也没确定理解的对不对~~ 这里请自行研究，欢迎讨论。

配置文件本身支持如字典，YAML等，欢迎找到更有效，更整洁的方式并更换。

日志目前是输出所有，且大小不受限制，并没有自动备份功能，但是根据```logging```文档这是可以控制并且暂时关闭的。 ~~我不想实验了，加油吧少年~~ 

## 0x02 ArknightsHelper 脚本启动
> 推荐安装 OCR 模块;感谢群友的贡献！关于 OCR 安装的文档可以查看 OCR_install.md

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

**注意：**请不要直接带入和你另一个设备同样的ADB_HOST，这样会导致连到另一台设备上去。

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
基本上里面的所有章节都测试过，但是总有一些奇奇怪怪的状况发生。并且请不要让你的自律翻车，不然就白给了。

```python
from Arknights import ArknightsHelper
from collections import OrderedDict

TASK_LIST = OrderedDict()
TASK_LIST['LS-4'] = 10
Ark = ArknightsHelper()
# True代表在任务完成后清理每日任务，False不清理,默认为false
Ark.main_handler(task_list=TASK_LIST,clear_tasks=True)
```
也可以直接调用 处理每日任务的函数
```python
# ...

Ark.clear_daily_task()
```

## 0x03 ArknightsHelper GUI

详见 release 分支下的文件


## 0x04 开机自启动批处理&一键开启

`start.bat`文件会启动模拟器并自动登录刷本，完成预定任务后关闭电脑，你也可以把它略作修改当做一键启动。如果想要使用这个批处理，需要以下几步：

1. 根据ArknightsAutoHelper的位置修改第5行和第7行的工作路径和盘符。
2. 根据自己设备的情况更改`start.bat`中的内容，每一行的作用我都注释出来了，主要就是改个模拟器的路径和密码。B服的小伙伴需要更改下“启动明日方舟”那行的`com.hypergryph.arknights/com.u8.sdk.U8UnityContext`。另外如果机器性能比较差，Timeout的延时也是需要修改的。
2. 编写`start.py`（这个文件是gitignore的）放到ArknightsAutoHelper里。
3. 把`start.bat`文件放到系统的“启动”目录下（不懂可以百度）。
4. 根据自己电脑的情况百度如何定时启动电脑，但你只要做完第三步它就会在每次开机的时候运行了，如果不需要它运行只要在批处理文件运行的前60秒内关掉它即可。

**注意：**“无限休眠”其实是有时间的，大概是1024秒，**提交这个批处理的时候我也将这个时间改成了 60 秒**，如果需要可以修改回来。

## 0x05 关于一些常见的问题

1. 分辨率/模拟器/路径问题
请往上看。
2. 我想跑一些别的关卡，但是提示我关卡不支持。
修改 click_location 中的 LIZHI_CONSUME，添加你需要的关卡。
此外，你添加的关卡只能通过 slim 模式来启动。
3. OCR 模块可以不装嚒？
可以不装，但是在使用脚本的时候请初始化理智值。目前而言，如果没有装 OCR 模块，你不能用 GUI 的版本。我之后会添加支持。
推荐安装 GUI 模块，因为这样能让一些地方的容错率变高。关于 OCR 的安装可以看文档。有人提议咱们可以用抓包来做。之后我会考虑这个功能，如果时间充裕的话（很显然是不充足的）
4. 我不会 python/我电脑里没装 Python，我能用这个嚒？
不能。我没有精力去给你整个 exe 文件。但是你也许可以通过我的代码学习一些 Python 的小技巧。
5. 之后会收费么？
不会，该项目一直开源。实际上作者还有别的事情要做，代码可能突然会有一段时间不更新了。欢迎来 pull 代码以及加群
6. 关于 mumu 模拟器的adb在哪里的问题
mumu 模拟器的 adb 不在模拟器的主路径下，而且它的名字叫 adb_server。mumu 模拟器自动隐藏了 adb 端口。
除非你是专业人士，否则**不建议使用 mumu 模拟器**。推荐使用夜神模拟器，群友也有用雷电模拟器的。

## 0x06 自定义开发与TODO

### 自定义开发与更多功能

详情请联系作者或者提出你的issue！祝大家玩的愉快

欢迎来加好友QQ 2454225341

也可以来加群[757689154](https://jq.qq.com/?_wv=1027&k=5298dGA)


![qrcode_1558871927006.jpg-60.7kB][3]


  [1]: http://static.zybuluo.com/shaobaobaoer/7ifp1acn3an7a3z23t96owt1/TIM%E6%88%AA%E5%9B%BE20190530114456.png
  [2]: http://static.zybuluo.com/shaobaobaoer/860t36w2ygsvet6sxn3lv3ty/TIM%E5%9B%BE%E7%89%8720190612102050.png
  [3]: http://static.zybuluo.com/shaobaobaoer/14ufv5gx72buoo1vyaa9jmgy/qrcode_1558871927006.jpg
