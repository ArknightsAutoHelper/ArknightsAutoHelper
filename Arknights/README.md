## Arknights 明日方舟 adb 辅助点击脚本

## 依赖

- OCR 模块

## 目前支持的启动方式

### main_handler
>  `main_handler` 包含了非完整的启动。也就是从首页面进行的各种操作

所需要的代码如下：

```python
from Arknights import ArknightsHelper
from collections import OrderedDict

TASK_LIST = OrderedDict()
TASK_LIST['CE-5'] = 5
TASK_LIST['4-8'] = 10
Ark = ArknightsHelper()
Ark.main_handler(task_list=TASK_LIST, clear_tasks=False)
# TASK_LIST [' 战斗章节 '] = 战斗次数
# True 代表在任务完成后清理每日任务，False 不清理

```

### main_battle_slim
> `main_battle_slim` 包含了不完整的战斗过程，也就是从你点击关卡开始的一系列操作

在此之前你需要把页面调整到类似于这样子：
![TIM截图20190513101009.png-1013.8kB][4]

所需要的代码如下:

```python
Ark = ArknightsHelper()
Ark.module_battle_slim(c_id='4-8', set_count=14, set_ai=True)
# c_id 是战斗章节
# set_count 是战斗次数
```

### OCR 模块未安装的操作方法

如果没有安装OCR模块，请在初始化ArknightsHelper()类时告知系统初值，就像这样子

```python
Ark = ArknightsHelper(123)
Ark.module_battle_slim(c_id='4-8', set_count=14, set_ai=True)
# "123" 指当前剩余理智
```

## 目前支持的关卡
芯片和日常，我感觉坐标点都是一样的么。

关于支持的关卡，可以查看`click_location.LIZHI_CONSUME`的相关信息。

------

【分割线】

------

## 烧包的苦逼开发日志

### 2018.4.30

我已经忘了抽了多少发了。新手20发抽完，也就保底一个5*+6*

### 2018.5.1

今天才是最气的。感觉自己非爆了。我可能今天一共抽了将近40发吧。把当初三测得时候冲得钱全花了

好的我感觉再抽下去要到保底线了。

一个6*都没有！都没有！而且

555群里一群海豹都在晒卡，我好酸，我想要能天使。附上自己当初随手截的一张图。酸死了


### 2018.5.2 

我居然再普通池子里除了一个6*... 可是安姐姐是个辅助啊喂喂

555可我现在还是只有两个个6星。我好惨啊。

我想要能天使小姐姐，我想要闪灵小姐姐。而且今天我把所有体力都拿去打龙门币了。没有芯片给小姐姐升级了。哭哭

![2019_5_2.jpg-133.1kB][2]

### 2018.5.3

我感觉我昨天抽的已经上了50发，然后一路到了保底线...于是除了一个盾姐姐（我好像忘了小姐姐叫啥了）

哎，辅助开发也陷入了点小问题。好像每日任务的坐标不是很好获取。之后可能要用Chinese OCR了。

===》

重点来了。下午失了智，氪了个20连。我昨天也抽了发10连，结果...连个五星都没有

今天失了智。又抽了20连。。。。。第一发是这样子

![feizhou_30_lian.jpg-922.5kB][3]

三个舔狗仿佛在嘲笑我有多非

好极了，再来一发。出了一个天火小姐姐。嗯没错，天火二宝了。

统计一下 30连一个5*。太坑了。。。。

太坑了！！！！

从群里加了几个非洲人，感觉又有感觉！



### 2018.5.9 

5.6号，刷出了一个高级资深TAG 出了一个夜莺

昨天出了一个小艾。但是我还是没有高星的物理输出，哭了

EMMM 好像很久没有COMMIT 新的代码了。游戏也不知不觉长草了。现在在精二的路上越走越远。

今天打算更新一点东西，包括了更加快速的战斗流程（当然，有时候网不好会出现不同步的问题）

以及全新的日常任务点击机制，可以在点击目录下看到我新写的一个字典文件。谁让所有的坐标都是一样的呢？
```python
DAILY_LIST = {
    3: {
        # __import__('datetime').datetime.now().strftime("%w")
        '4':
            {
                'A': 1,
                'C': 2,
            }
    },
    2: {
        '1':
            {
                'LS': 0,
            },
        }
}
```

于是乎今天碎了10块石头去刷材料。希望赶紧精二吧。

### 2018.5.10

找到了着迷网上的一些信息，更新了位置坐标。现在可以根据日期定位了。

更加智能化的操作，增加了4图的辅助部分，现在会判断图的位置来选择座标了。

### 2018.5.11
想让每次点击的内容不一样。写起来问题还挺大的，目前还在更新中...

增加了OCR的自检测模块。现在可以不用OCR进行战斗了，但是可能会有系统错误的风险

### 2018.5.13

更新了SLIM 模块，可以帮你快速启动。在此之前你需要把页面调整到如下的样子：

![TIM截图20190513101009.png-1013.8kB][4]

之后通过这样的代码就可以迅速开始战斗，你可以手动选关。并且理论上该模块比完整的模块稳定并且不容易被系统检测。

```python
Ark = ArknightsHelper()
Ark.module_battle_slim(c_id='4-8', set_count=8)
```

你可以比较懒，不点代理指挥，在此之前传入参数
```python
Ark.module_battle_slim(c_id='4-8', set_count=8,set_ai=True)
```
即可让系统帮你点代理指挥
祝刷的愉快


### 2018.5.18

好像好久不来写点README了，现在辅助的开发已经基本没有问题了，支持了绝大部分关卡。
今天重构了一下战斗部分的代码逻辑，我把slim模式给嵌套进去了，但是在故障处理方面还是颇为困难。。。毕竟要考虑的事情很多。

另外我也精二了两个角色啦一个推王一个天火，目前开始护肝了，也就是不碎石头换体力了。
不得不承认，精二立绘真棒！



  [2]: http://static.zybuluo.com/shaobaobaoer/wqtlavh1zul8s08h0my417z2/2019_5_2.jpg
  [3]: http://static.zybuluo.com/shaobaobaoer/zdgezifv1tjtmzhz9kdfoshh/feizhou_30_lian.jpg
  [4]: http://static.zybuluo.com/shaobaobaoer/27owy5sd99gk0ciqzgdrnnee/TIM%E6%88%AA%E5%9B%BE20190513101009.png
