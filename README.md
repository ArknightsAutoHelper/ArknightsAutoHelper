# Arknights Auto Helper

> 明日方舟辅助脚本，分支说明如下

| 分支    | 说明    |
|:----|:----|
| master |~~开发者认为的~~ 稳定版本|
| dev |开发、测试新功能的分支|
|release |目前可以应用的GUI版本|
| shaobao_adb |经过封装可以移植的ADB方法类|

功能说明：

* 自动重复刷图，使用理智药、~~碎石~~
    * 识别掉落物品，上传企鹅物流数据统计
* 自动选图（从主界面开始到关卡信息界面）
* 自动领取任务奖励
* 公开招募识别
* 基建查房、一键领取（部分）

## 0x01 运行须知

### **安装**

#### 从源代码安装
```bash
git clone https://github.com/ninthDevilHAUNSTER/ArknightsAutoHelper
cd ArknightsAutoHelper

#### 建议使用 venv 避免依赖包冲突
python3 -m venv venv
# 在 Windows cmd 中：
venv\Scripts\activate.bat
# 在 PowerShell 中：
& ./venv/[bS]*/Activate.ps1
# 在 bash/zsh 中：
source venv/bin/activate
#### venv end

pip install -r requirements.txt
```

#### 二进制包（Windows）

从 Actions artifacts 中下载 PyInstaller 打包后的二进制包，二进制包随源代码同步更新。

[![make PyInstaller packaged release](https://github.com/ninthDevilHAUNSTER/ArknightsAutoHelper/workflows/make%20PyInstaller%20packaged%20release/badge.svg?branch=master)](https://github.com/ninthDevilHAUNSTER/ArknightsAutoHelper/actions?query=workflow%3A%22make+PyInstaller+packaged+release%22+is%3Asuccess)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FninthDevilHAUNSTER%2FArknightsAutoHelper.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FninthDevilHAUNSTER%2FArknightsAutoHelper?ref=badge_shield)

#### OCR 依赖
目前 OCR 用于：

* 公开招募 tag 识别
* 对话框内容识别（如基建退出提示）

如果 OCR 不可用，则不能自动处理以上情况。

目前可以使用 tesseract（需另行安装）、Windows OCR（需要 Windows 10 简体中文系统或语言包）和百度 OCR API，请参阅 [OCR 安装说明](https://github.com/ninthDevilHAUNSTER/ArknightsAutoHelper/wiki/OCR-%E5%AE%89%E8%A3%85%E8%AF%B4%E6%98%8E)。


###  **环境与分辨率**
> 💡 由于游戏内文字渲染机制问题，分辨率过低可能影响识别效果，建议分辨率高度 1080 或以上。

大部分功能可以自适应分辨率（宽高比不小于 16:9，即`宽度≥高度×16/9`），作者测试过的分辨率有 <span style="opacity: 0.5">1280x720、1440x720、</span>1920x1080、2160x1080。

例外（欢迎提交代码改进）：
* 基建收菜（需要 16:9 宽高比和特定基建布局）
* 好友查房（需要 16:9 宽高比）
* 自动登录游戏（需要 1280x720 分辨率）

### **ADB 连接**

请确认 `adb devices` 中列出了目标模拟器/设备：

    $ adb devices
    emulator-5554   device

如何连接 ADB 请参考各模拟器的文档、论坛等资源。

如果 `adb devices` 中列出了目标模拟器/设备，但脚本不能正常连接，或遇到其他问题，请尝试使用[最新的 ADB 工具](https://developer.android.google.cn/studio/releases/platform-tools)。

#### 常见问题

* 部分模拟器（如 MuMu、BlueStacks）需要自行启动 ADB server。
* 部分模拟器（如 MuMu）不使用标准模拟器 ADB 端口，ADB server 无法自动探测，需要另行 adb connect。
* 部分模拟器（如夜神）会频繁使用自带的旧版本 ADB 挤掉用户自行启动的新版 ADB。

可以参阅[配置说明](#额外设置)以配置自动解决以上问题。

### **额外设置**

关于额外设置请移步到 [config/config-template.yaml](config/config-template.yaml) 中查看

#### **日志说明**
运行日志（文本）采用```import logging```在log目录下生成**ArknightsAutoHelper.log**推荐用Excel打开，分割符号为“!”

相关配置文件在```config```目录下的**logging.yaml**，由于过于复杂 ~~其实也没确定理解的对不对~~ 这里请自行研究，欢迎讨论

日志目前启动按照时间自动备份功能，间隔为一天一次，保留最多7份。

图像识别日志为 `log/*.html`，相应识别模块初始化时会清空原有内容。

多开时日志文件名会出现实例 ID，如 `ArknightsAutoHelper.1.log`。

**报告 issue 时，建议附上日志以便定位问题。**

## 0x02 ArknightsHelper 命令行启动

> 💡 Windows：命令行功能在 Windows 10 1607 (build 14393) 及以上版本上体验最佳。非简体中文系统可能无法在 Windows 命令行窗口中正确显示简体中文文字，可尝试使用 Windows Terminal。

### 命令行启动说明

```
$ python3 akhelper.py
usage: akhelper.py command [command args]
commands (prefix abbreviation accepted):
    quick [+-rR[N]] [n]
        重复挑战当前画面关卡特定次数或直到理智不足
        +r/-r 是否自动回复理智，最多回复 N 次
        +R/-R 是否使用源石回复理智（需要同时开启 +r）
    auto [+-rR[N]] stage1 count1 [stage2 count2] ...
        按顺序挑战指定关卡特定次数直到理智不足
    collect
        收集每日任务奖励
    recruit [tags ...]
        公开招募识别/计算，不指定标签则从截图中识别
    interactive
        进入交互模式，减少按键次数（
    help
        输出本段消息
```

命令可使用前缀（首字母）缩写（类似 Linux iproute2），交互模式下只需输入对应命令名称即可，如：

```
$ python3 akhelper.py q 5

$ python3 akhelper.py i
akhelper> q 5
    ...
akhelper> c
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
python3 akhelper.py quick -r
# 重复刷当前画面关卡，禁用自动回复理智（直到理智不足停止）
python3 akhelper.py quick +r5
# 重复刷当前画面关卡，启用自动回复理智，最多回复 5 次
python3 akhelper.py quick +rR 99
# 重复刷当前画面关卡 99 次，启用自动回复理智，启用碎石回复理智
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

\* 该模块支持关卡有限，请等待后续更新

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


## 0x06 已知问题

* 自动选关功能：点击随机偏移范围大小固定，且与分辨率无关
* 某些情况下，物品、数量识别会出错


## 0x07 自定义开发与TODO

### 关于一些常见的问题

#### 1. 分辨率/模拟器/路径问题

☞ [环境与分辨率](#环境与分辨率)

#### 2. 我想跑一些别的关卡，但是提示我关卡不支持。

这些关卡可以通过 ~~slim~~ quick 模式来启动。

#### 3. OCR 模块可以不装嚒？

最好安装，在之后的版本迭代中会对没有OCR依赖的用户越来越不友好

#### 4. 我不会python|我电脑里没装Python，我能用这个嚒？

可以使用[二进制包](#二进制包windows)

#### 5. 之后会收费么？

不会，该项目一直开源。实际上作者还有别的事情要做，代码可能突然会有一段时间不更新了。欢迎来pull代码以及加群

#### 6. ~~关于mumu模拟器的adb在哪里的问题~~【目前已经解决】

☞ [常见问题](#常见问题)

#### 7. 我想将这个脚本适配到其他服务器

☞ [Porting to Another Server](https://github.com/ninthDevilHAUNSTER/ArknightsAutoHelper/wiki/Porting-to-Another-Server)

### 自定义开发与更多功能

详情请联系作者或者提出你的issue！祝大家玩的愉快

欢迎来加开发者QQ 2454225341 或加入QQ群 757689154

  [1]: http://static.zybuluo.com/shaobaobaoer/7ifp1acn3an7a3z23t96owt1/TIM%E6%88%AA%E5%9B%BE20190530114456.png
  [2]: http://static.zybuluo.com/shaobaobaoer/860t36w2ygsvet6sxn3lv3ty/TIM%E5%9B%BE%E7%89%8720190612102050.png
  [3]: http://static.zybuluo.com/shaobaobaoer/14ufv5gx72buoo1vyaa9jmgy/qrcode_1558871927006.jpg


## License
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FninthDevilHAUNSTER%2FArknightsAutoHelper.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2FninthDevilHAUNSTER%2FArknightsAutoHelper?ref=badge_large)