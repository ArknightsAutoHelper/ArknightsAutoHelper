## 根据 `aog.wiki` 上的推荐刷库存中最少的蓝材料

> 根据 `aog.wiki` 上的推荐刷库存中最少的蓝材料

长草时用的脚本, 检查库存中最少的蓝材料, 然后去 aog 上推荐的地图刷材料.

aog 地址: https://arkonegraph.herokuapp.com/

不想的刷的材料可以修改脚本中的 exclude_names.

cache_key 控制缓存的频率, 默认每周读取一次库存, 如果需要手动更新缓存, 
直接删除目录下的 aog_cache.json 和 inventory_items_cache.json 即可.

只刷常规关卡, 活动关卡不刷.

可以尝试将 `config/config.yaml` 中的 `behavior/use_ocr_goto_stage` 修改为 true 以支持更多的关卡跳转


### 使用方法

运行 `整合工具箱.bat` 中的 `刷库存中最少的蓝材料` 选项即可.
