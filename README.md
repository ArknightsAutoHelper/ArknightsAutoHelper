# Arknights Auto Helper

> 明日方舟辅助脚本，分支说明如下

| 分支    | 说明    |
|:----|:----|
| master |目前的稳定版本|
|release |目前可以应用的GUI版本|
| dev |目前的开发版本|
| shaobao_adb |经过封装可以移植的ADB方法类|

## 0x01 运行须知

###  **环境与分辨率**

该辅助需要安卓模拟器并将分辨率设置为

⚠ ` 1280*720` ⚠ 分辨率设置非常重要 ⚠

由于作者精力有限，只做了绝对坐标的，欢迎大家重写模块。建议使用夜神模拟器，记得开启开发者模式。

\* 部分模块已经可以自适应分辨率和宽高比（大于 16:9），作者测试过的分辨率有 1280x720、1440x720、1920x1080、2160x1080。

### **ADB 连接**

虽然脚本不依赖 `adb` 工具进行操作，但是依然需要 ADB server 连接到模拟器/设备，请确认 `adb devices` 中列出了目标模拟器/设备。如何连接 ADB 请参考各模拟器的文档、论坛等资源。

如果 `adb devices` 中列出了目标模拟器/设备，但脚本不能正常连接，或遇到其他问题，请尝试使用[最新的 ADB 工具](https://developer.android.google.cn/studio/releases/platform-tools)。

目前暂不考虑直接连接到模拟器/设备的 ADB over TCP/IP 或 USB 端口，因为 ADB daemon 不支持同时存在多个连接，需要 ADB server 进行复用。

### **安装依赖**

#### Python 依赖
```bash
$ pip install -r requirements.txt
```

#### OCR 依赖
<details><summary>目前仅公开招募识别依赖外部 OCR，展开查看</summary>

该辅助需要安装本地OCR工具（tesseract），Windows OCR（需要安装简体中文和英文语言包）或者申请百度OCR

**关于本地OCR工具安装可查看**
https://github.com/ninthDevilHAUNSTER/ArknightsAutoHelper/blob/master/OCR_install.md

**关于百度OCR申请**

> 百度普通的文字识别免费为50000次/日，可以开通付费，超过免费调用量后，根据百度文字识别文档，会暂停使用，建议使用前阅读文档，不保证政策是否改变。理论上每天次数非常充足

文档地址：https://cloud.baidu.com/doc/OCR/index.html
启用百度api作为ocr识别方案，需要自行注册百度云。并在 `config.yaml` 中配置
```yaml
ocr:
  # 选择 OCR 引擎，非必要
  # 设置为 auto 则选择下列第一个可用的引擎: tesseract, windows_media_ocr, baidu
  engine: baidu
  # 百度 API 设置，使用 baidu OCR 时需要正确填写
  baidu_api:
    # 是否将百度 OCR 标记为可用
    enabled: true
    # 百度 API 鉴权数据
    app_id: '你的 App ID'
    app_key: '你的 Api Key'
    app_secret: '你的 Secret Key'
```

**关于Windows OCR**

需要 Windows 10。

当前默认配置为在 tesseract 无法使用（未安装）时使用。如要强制使用，请更改如下
```yaml
ocr:
  engine: windows_media_ocr
```
Windows OCR 的语言数据是随语言支持安装的，可能需要在系统语言列表中加入英语（美国）以安装英语 OCR 支持。


目前 Windows OCR 无法识别游戏中部分文本，正在考虑使用替代方法。
</details>

### **额外设置**

关于额外设置请移步到 config/README.md中查看

#### **日志说明**

日志采用```import logging```在log目录下生成**ArknightsAutoHelper.log**推荐用Excel打开，分割符号为“!”

相关配置文件在```config```目录下的**logging.yaml**，由于过于复杂 ~~其实也没确定理解的对不对~~ 这里请自行研究，欢迎讨论

日志目前启动按照时间自动备份功能，间隔为一天一次，保留最多7份。

## 0x02 ArknightsHelper 命令行启动

### 命令行启动说明

```
$ python3 akhelper.py
usage: akhelper.py command [command args]
commands:
    quick [n]
        重复挑战当前画面关卡特定次数或直到理智不足
    auto stage1 count1 [stage2 count2] ...
        按顺序挑战指定关卡特定次数直到理智不足
    collect
        收集每日任务奖励
    recruit
        公开招募识别/计算，不指定标签则从截图中识别
    help
        输出本段消息
```

<details><summary>旧版命令行接口</summary>

```bash
Usage: ArknightsShell.py [options] arg1 arg2 ...

Options:
  -h, --help            显示帮助
  -s, --module-battle-slim
                        简略战斗模块，请确保页面停留正确
  -b, --module-battle   主战斗模块
  -t TASK_LIST, --task-list=TASK_LIST
                        战斗清单，输入格式: 
                        用 | 分隔任务序列，最后一个|不需要输入
                        用 : 分隔关卡名和次数
                        e.g.:
                            LS-5:10|CE-5:1
  -c, --clear-daily     任务执行完毕后自动领取奖励

```

**致各位贡献者**：新功能请优先加到新命令行接口
</details>

### 简略战斗模块

快速启动模块需要手动选关。到如下画面，活动关卡你也可以这么刷。

\* 该模块可以自适应分辨率

![TIM截图20190513101009.png-1013.8kB][1]

```bash
python3 akhelper.py quick 99
# 重复刷当前画面关卡 99 次，也可以不指定次数
```

<details><summary>旧版命令行接口</summary>

```bash
$ python ArknightsShell.py -s -t slim:99
# 由于是快速启动模式，所以只会执行第一项任务清单，额外输入的任务序列会被忽略。
```

</details>

*注意*

* 该模块会识别当前理智和关卡理智消耗，理智不足时会自动停止或补充理智（需在配置中启用）
* 理论上该模块比完整的模块稳定并且不容易被系统检测。并且该模块所有的点击序列都是随机化的，不容易被检测


### 主战斗模块

主战斗模块可以从几乎任何位置（理论上有返回键的页面）开始任务序列。

\* 该模块支持关卡有限，且仅支持 1280x720 分辨率，请等待后续更新

```bash
python3 akhelper.py auto   5-1 2   5-2 3
# 按顺序刷 5-1 关卡 2 次，5-2 关卡 3 次
```

<details><summary>旧版命令行接口</summary>

```bash
$ python ArknightsShell.py -b -t 5-1:2|5-2:3
```

</details>

## 0x03 ArknightsHelper 自定义脚本启动

请阅读 ArknightsHelper_examples.py.txt 下的代码并编写自定义脚本

## 0x04 ArknightsHelper GUI 启动

详见 release 分支下的文件

## 0x05 开机自启动批处理&一键开启

`start.bat`文件会启动模拟器并自动登录刷本，完成预定任务后关闭电脑，你也可以把它略作修改当做一键启动。如果想要使用这个批处理，需要以下几步：

1. 根据ArknightsAutoHelper的位置修改第5行和第7行的工作路径和盘符。
2. 根据自己设备的情况更改`start.bat`中的内容，每一行的作用我都注释出来了，主要就是改个模拟器的路径和密码。B服的小伙伴需要更改下“启动明日方舟”那行的`com.hypergryph.arknights/com.u8.sdk.U8UnityContext`。另外如果机器性能比较差，Timeout的延时也是需要修改的。
2. 编写`start.py`（这个文件是gitignore的）放到ArknightsAutoHelper里。
3. 把`start.bat`文件放到系统的“启动”目录下（不懂可以百度）。
4. 根据自己电脑的情况百度如何定时启动电脑，但你只要做完第三步它就会在每次开机的时候运行了，如果不需要它运行只要在批处理文件运行的前60秒内关掉它即可。

注意：“无限休眠”其实是有时间的，大概是1024秒，**提交这个批处理的时候我也将这个时间改成了60秒**，如果需要可以修改回来。



## 0x06 自定义开发与TODO

### 关于一些常见的问题

1. 分辨率/模拟器/路径问题
请看README
2. 我想跑一些别的关卡，但是提示我关卡不支持。
这些关卡可以通过slim模式来启动。目前主战斗模块并不支持所有的关卡
3. OCR 模块可以不装嚒？
最好安装，在之后的版本迭代中会对没有OCR依赖的用户越来越不友好
4. 我不会python|我电脑里没装Python，我能用这个嚒？
可以，请下载release分支下经过PyInstaller 打包后的exe 文件。如果有问题欢迎来群里提问
5. 之后会收费么？
不会，该项目一直开源。实际上作者还有别的事情要做，代码可能突然会有一段时间不更新了。欢迎来pull代码以及加群
6. ~~关于mumu模拟器的adb在哪里的问题~~【目前已经解决】
mumu模拟器的adb不在模拟器的主路径下，而且它的名字叫adb_server。mumu模拟器自动隐藏了adb端口。
除非你是专业人士，否则不建议使用mumu模拟器。推荐使用夜神模拟器，群友也有用雷电模拟器的。


### 自定义开发与更多功能

详情请联系作者或者提出你的issue！祝大家玩的愉快

欢迎来加开发者QQ 2454225341 或加入QQ群 757689154

  [1]: http://static.zybuluo.com/shaobaobaoer/7ifp1acn3an7a3z23t96owt1/TIM%E6%88%AA%E5%9B%BE20190530114456.png
  [2]: http://static.zybuluo.com/shaobaobaoer/860t36w2ygsvet6sxn3lv3ty/TIM%E5%9B%BE%E7%89%8720190612102050.png
  [3]: http://static.zybuluo.com/shaobaobaoer/14ufv5gx72buoo1vyaa9jmgy/qrcode_1558871927006.jpg
