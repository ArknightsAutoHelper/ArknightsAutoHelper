## 1. 创建操作记录


执行 helper 的 create_custom_record 方法, 目前仅在 mumu 模拟器上进行了测试.

```python
from Arknights.helper import ArknightsHelper

if __name__ == '__main__':
    helper = ArknightsHelper()
    helper.create_custom_record('test')
```

### create_custom_record 参数说明

 - record_name 记录名称
 - roi_size 截图大小, 默认 64
 - wait_seconds_after_touch 执行点击后等待的时间, 默认 1
 - description 记录描述, 默认无
 - back_to_main 是否在执行记录前返回主界面, 默认 true
 - prefer_mode 点击使用的默认模式, match_template 目标匹配模式, point 坐标模式, 默认 match_template

生成的记录保存在 `custom_record` 下相应的文件夹中.

### records 参数说明

```json
{
    "img": "step3.png",           # 记录对应的模板图像
    "point": [                    # 点击坐标
        1165,
        626
    ],
    "type": "tap",
    "wait_seconds_after_touch": 5,
    "repeat": 11,                 # 重复次数, 默认为 1
    "raise_exception": false,     # 未匹配时是否抛出异常, 默认 true
    "threshold": 0.95             # 匹配相似度阈值, 默认 0.7
}
```


### 注意事项


 - wait_seconds_after_touch 默认为 1, 点击后请等待一段时间, 待控制台出现 `go ahead...` 后再进行下一次点击.

 - 滑动屏幕可以退出记录.

 - 图片背景可能会影响匹配精度, 如果截图过大可以用画图工具把图片截小一点.

 - 如果需要更精细地控制每一步操作, 可以手工编辑 `record.json` 文件.


## 2. 使用操作记录


<details><summary>收信用点</summary>

```python
from Arknights.helper import ArknightsHelper


if __name__ == '__main__':
    helper = ArknightsHelper()
    helper.replay_custom_record('get_credit')
```

</details>
