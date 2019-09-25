# 关于图像识别模块中使用的坐标

为了适应不同的分辨率，图像识别模块中使用了基于视口宽度和高度的坐标系统（参考 CSS 中的 vw, vh)

即：
* 截图的宽度为 `100*vw`
* 截图的高度为 `100*vh`

另外，游戏中大部分 UI 元素的大小与视口高度有关，在水平方向上则采用左对齐、居中和右对齐。因此我们可以采用 `vw` 和 `vh` 的线性组合来定义 UI 元素的坐标，例如：
* 返回按钮（左对齐）：`(3.194*vh, 2.222*vh, 20.972*vh, 7.917*vh)`
* 体力数值（右对齐）：`(100*vw - 22.917*vh, 2.917*vh, 100*vw, 8.194*vh)`
* 领取任务按钮（居中）：`(50*vw+49.630*vh, 16.019*vh, 50*vw+83.704*vh, 23.565*vh)`

\* 元组中的四个值分别为左边、顶边、右边和底边

\* 部分 UI 元素不遵循以上定位规律，如主菜单。对于此类 UI 元素，可以在特定宽高比下仅使用 `vw` 定义横向坐标，`vh` 定义纵向坐标。若要使用此定位方法，请加入宽高比 assertion，如:
```python
from fractions import Fraction

aspect = Fraction(*img.size)
vw, vh = util.get_vwvh(img)
if aspect == Fraction(16, 9):
    return (a1*vw, b1*vh, c1*vw, d1*vh)
elif aspect == Fraction(18, 9):
    return (a2*vw, b2*vh, c2*vw, d2*vh)
else:
    raise NotImplementedError('unsupported aspect ratio')
```

[Arknights/dev_tools/cropper.html](../Arknights/dev_tools/cropper.html) 工具可以协助进行取点和截取模板图片。选取坐标并更换不同分辨率的图片后，会重新计算并显示对应的绝对坐标。
