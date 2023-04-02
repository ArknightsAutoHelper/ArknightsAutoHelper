# ![icon](webgui2/public/carrot.png) Arknights Auto Helper

明日方舟辅助脚本

功能说明：

* 自动重复刷图，使用理智药、~~碎石~~
    * 识别掉落物品，上传企鹅物流数据统计
* 自动选图（从主界面开始到关卡信息界面）
* 自动领取任务奖励
* 公开招募识别

## 0x01 运行须知

### 二进制包（Windows）

⬇️ 从 Releases 中下载 [二进制包启动器](https://github.com/ArknightsAutoHelper/ArknightsAutoHelper/releases/tag/bootstrapper-release)。

首次运行启动器时，将从 GitHub 下载通过 Actions 打包的最新代码及运行环境，请保持网络畅通。

运行 `akhelper.exe --update` 或 `akhelper-gui.exe --update` 可更新到最新版本。如果最新版本存在问题，可尝试从 [Actions](https://github.com/ArknightsAutoHelper/ArknightsAutoHelper/actions) 中下载 90 天内的旧版本覆盖 `.bootstrapper` 目录内的对应文件。

### 从源代码安装

> ⚠ **不建议使用 GitHub 的 Download ZIP 功能下载源码包**：这样做会丢失版本信息，且不便于后续更新。

请参考 [wiki/从源代码安装]。

###  环境与分辨率
> 💡 由于游戏内文字渲染机制问题，分辨率过低可能影响识别效果，建议分辨率高度 1080 或以上。

大部分功能可以自适应分辨率（宽高比不小于 16:9，即`宽度≥高度×16/9`），作者测试过的分辨率有 <span style="opacity: 0.5">1280x720、1440x720、</span>1920x1080、2160x1080。

### ADB 连接

请确认 `adb devices` 中列出了目标模拟器/设备：
```console
$ adb devices
emulator-5554   device
```
如何连接 ADB 请参考各模拟器的文档、论坛等资源。

如果 `adb devices` 中列出了目标模拟器/设备，但脚本不能正常连接，或遇到其他问题，请尝试使用[最新的 ADB 工具](https://developer.android.google.cn/studio/releases/platform-tools)。

#### 常见问题

##### ADB server 相关

* 部分模拟器（如 MuMu、BlueStacks）需要自行启动 ADB server。
* 部分模拟器（如 MuMu、BlueStacks Hyper-V）不使用标准模拟器 ADB 端口，ADB server 无法自动探测，需要另行 adb connect。
* 部分模拟器（如夜神）会频繁使用自带的旧版本 ADB 挤掉用户自行启动的新版 ADB。

可以参阅[配置说明](#额外设置)以配置自动解决以上问题。

##### 其他

* 部分非 VMM 模拟器（声称“不需要开启 VT”，如 MuMu 星云引擎）不提供 ADB 接口。

### **额外设置**

关于额外设置请移步到 [config/config-template.yaml](config/config-template.yaml) 中查看

#### **日志说明**
运行日志（文本）采用```import logging```在log目录下生成**ArknightsAutoHelper.log**推荐用Excel打开，分割符号为“!”

相关配置文件在```config```目录下的**logging.yaml**，由于过于复杂 ~~其实也没确定理解的对不对~~ 这里请自行研究，欢迎讨论

日志目前启动按照时间自动备份功能，间隔为一天一次，保留最多7份。

图像识别日志为 `log/*.html`，相应识别模块初始化时会清空原有内容。

多开时日志文件名会出现实例 ID，如 `ArknightsAutoHelper.1.log`。

**报告 issue 时，建议附上日志以便定位问题。**

## 0x02 ArknightsHelper GUI 启动
> 💡 Windows：如果您按照 [wiki/从源代码安装] 配置了 venv，则可以通过双击 `启动GUI.bat` 调用。
```console
$ python3 akhelper-gui.pyw
```

Web GUI 将在一下第一个可用的浏览器环境中打开：

* 内嵌浏览器
* Google Chrome、Chromium、Microsoft Edge 的 PWA 模式*
* 系统默认浏览器*

<small>* 使用外部浏览器时，HTTP 服务器将在最后一个连接关闭后 3 分钟内退出。</small>

## 0x03 ArknightsHelper 命令行启动

> 💡 Windows：命令行功能在 Windows 10 1607 (build 14393) 及以上版本上体验最佳。非简体中文系统可能无法在 Windows 命令行窗口中正确显示简体中文文字，可尝试使用 Windows Terminal。

### 命令行启动说明
> 💡 Windows：如果您按照 [wiki/从源代码安装] 配置了 venv，则可以通过双击 `整合工具箱(新).bat` 调用。
```console
$ python3 akhelper.py
usage: akhelper.py command [command args]
    connect [connector type] [connector args ...]
        连接到设备
        支持的设备类型：
        connect adb [serial or tcpip endpoint]
    quick [+-rR[N]] [n]
        重复挑战当前画面关卡特定次数或直到理智不足
        +r/-r 是否自动回复理智，最多回复 N 次
        +R/-R 是否使用源石回复理智（需要同时开启 +r）
    auto [+-rR[N]] TARGET_DESC [TARGET_DESC]...
        按顺序挑战指定关卡。
        TARGET_DESC 可以是：
            1-7 10      特定主线、活动关卡（1-7）10 次
            grass       一键长草: 检查库存中最少的蓝材料, 然后去 aog 上推荐的地图刷材料
            plan        执行刷图计划: 使用 arkplanner 命令创建刷图计划。执行过程会自动更新计划进度。
    recruit [tags ...]
        公开招募识别/计算，不指定标签则从截图中识别
    collect
        收集每日任务和每周任务奖励
    record
        操作记录模块，使用 record --help 查看帮助。
    riic <subcommand>
        基建功能（开发中）
        riic collect
        收取制造站及贸易站
        riic shift <room> <operator1> <operator2> ...
        指定干员换班
        room: B101 B102 B103 B201 B202 B203 B301 B302 B303 dorm1 dorm2 dorm3 dorm4 meeting workshop office
    arkplanner
        输入材料需求创建刷图计划。使用 auto plan 命令执行刷图计划。
```

> 如果你的电脑配置有 [Windows 终端](https://github.com/microsoft/terminal)（Windows 11已内置）和  [PowerShell Core](https://github.com/PowerShell/PowerShell)，可通过在 Windows Terminal - 设置 中增加如下配置即可一键启动命令行：
> 1. 打开 Windows Terminal，点击顶部 `+` 按钮旁 `ˇ` 按钮下拉菜单，打开**设置**；
> 2. 点击 **添加新配置文件**，新建空配置文件；
> 3. 填写配置名称（例如 `Arknights Auto Helper`）；
> 4. 命令行填写：
> ```powershell
> pwsh.exe -NoExit -Command "& '项目路径\venv\Scripts\Activate.ps1'; python 'akhelper.py'"
> ```
> 5. 启动目录填写**项目路径**，否则命令行中的 `akhelper.py` 需要替换为绝对路径；
> 6. （可选）图标路径设置为 `项目路径\webgui2\dist\carrot.png`。
> 
> 配置完毕后即可在 `Windows 终端` 中跳过激活虚拟环境的步骤直接启动 akhelper。

命令可使用前缀（首字母）缩写（类似 Linux iproute2），交互模式下只需输入对应命令名称即可，如：

```console
$ python3 akhelper.py q 5

$ python3 akhelper.py i
akhelper> q 5
    ...
akhelper> c
```

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

*注意*

* 该模块会识别当前理智和关卡理智消耗，理智不足时会自动停止或补充理智（需在配置中启用）
* 理论上该模块比完整的模块稳定并且不容易被系统检测。并且该模块所有的点击序列都是随机化的，不容易被检测


### 主战斗模块

1. 主战斗模块可以从几乎任何位置（理论上有返回键的页面）开始任务序列。

\* 该模块支持主线章节大部分关卡。

```bash
python3 akhelper.py auto   5-1 2   5-2 3
# 按顺序刷 5-1 关卡 2 次，5-2 关卡 3 次
```

### 通过输入所需材料数量创建刷图计划并执行

`arkplanner` 命令可以通过企鹅物流的接口, 根据输入的材料创建刷图计划 (支持自动获取当前库存):

```
# 缓存将在第一次启动脚本时创建, 如果没有新的地图或材料, 这个缓存没必要更新.
是否刷新企鹅物流缓存(缓存时间: ....)[y/N]:
材料列表：
序号: 0, 材料等级: 3, 名称: 赤金
序号: 1, 材料等级: 3, 名称: 提纯源岩
...
...
# 需要 10 个提纯源岩
材料序号/需求数量(输入为空时结束):1/10
材料序号/需求数量(输入为空时结束):

# 默认 n, 输入 y 将自动读取游戏中的库存, 并加入到刷图计划的计算中
是否获取当前库存材料数量(y,N):y

刷图计划:
关卡 [...] 次数 2
...
预计消耗理智: ...
刷图计划已保存至: config/plan.json
```

`auto plan` 文件将从上一步生成的 config/plan.json 获取并执行刷图计划. 

如果当前的理智不足以完成刷图计划, 将保存已经刷图的次数, 并在下次运行时恢复.

如果完成刷图计划后, 当前的理智可能还有剩余，可以使用其他命令消耗剩余理智（如使用脚本连续运行命令）。

## 0x04 ArknightsHelper 自定义脚本启动

请参考 [scripting_example.pyi](scripting_example.pyi) 编写自定义脚本。

## 0x05 已知问题

* 自动选关功能：点击随机偏移范围大小固定，且与分辨率无关
* 某些情况下，物品、数量识别会出错

## 0x06 自定义开发与TODO

如果您已经有一定的 Python 基础，可以通过 [wiki 中的开发文档](https://github.com/ArknightsAutoHelper/ArknightsAutoHelper/wiki/Development-%23-1.-Getting-Started)快速上手。

### 关于一些常见的问题

#### 1. 分辨率/模拟器/路径问题

☞ [环境与分辨率](#环境与分辨率)

#### 2. 我想跑一些别的关卡，但是提示我关卡不支持。

这些关卡可以通过 quick 命令来启动。

#### 3. OCR 模块可以不装嚒？

~~最好安装，在之后的版本迭代中会对没有OCR依赖的用户越来越不友好~~不可以。

#### 4. 我不会python|我电脑里没装Python，我能用这个嚒？

可以使用[二进制包](#二进制包windows)

#### 5. 之后会收费么？

不会，该项目一直开源。实际上作者还有别的事情要做，代码可能突然会有一段时间不更新了。欢迎来pull代码以及加群

#### 6. ~~关于mumu模拟器的adb在哪里的问题~~【目前已经解决】

☞ [常见问题](#常见问题)

#### 7. 我想将这个脚本适配到其他服务器

☞ [Porting to Another Server](https://github.com/ArknightsAutoHelper/ArknightsAutoHelper/wiki/Porting-to-Another-Server)

### 自定义开发与更多功能

详情请联系作者或者提出你的issue！祝大家玩的愉快

欢迎来加开发者QQ 2454225341 或加入QQ群 757689154 [Telegram 群（有简单防爬虫验证）](https://t.me/+fBBb553wouM5MWM1)

  [1]: http://static.zybuluo.com/shaobaobaoer/7ifp1acn3an7a3z23t96owt1/TIM%E6%88%AA%E5%9B%BE20190530114456.png
  [2]: http://static.zybuluo.com/shaobaobaoer/860t36w2ygsvet6sxn3lv3ty/TIM%E5%9B%BE%E7%89%8720190612102050.png
  [3]: http://static.zybuluo.com/shaobaobaoer/14ufv5gx72buoo1vyaa9jmgy/qrcode_1558871927006.jpg
  [wiki/从源代码安装]: https://github.com/ArknightsAutoHelper/ArknightsAutoHelper/wiki/%E4%BB%8E%E6%BA%90%E4%BB%A3%E7%A0%81%E5%AE%89%E8%A3%85