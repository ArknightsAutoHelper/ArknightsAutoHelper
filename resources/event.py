from typing import Tuple, List

EXTRA_KNOWN_ITEMS = [
    '龙门币1500',
    '家具',
    '龙门币2000',
    '龙门币1000',
    '资质凭证'
]

FIXED_QUANTITY = [
    '量子二踢脚',
    '食堂汤点券',
    '无名的识别牌',
    '彼得海姆热销饼干',
    '老旧贵族领铸币',
    '机械零件',
    '废弃时钟表盘',
    '赏金猎人金币(2020)',
    '梅什科竞技证券',
    '工厂铁片',
    '奇景明信片',
    '夕墨',
    '罗德岛物资配给证书',
]

# ONE_OR_NONE = [
#     '应急理智小样',
#     '罗德岛物资补给',
#     '岁过华灯',
#     '32h战略配给',
#     '感谢庆典物资补给',
# ]

def event_preprocess(stage: str, items: List[Tuple[str, str, int]], exclude_from_validation: List):
    # [('常规掉落', '固源岩', 1), ...]
    for itemrecord in items:
        group, name, qty = itemrecord

        if name in FIXED_QUANTITY:
            # 不加入汇报列表
            continue
            
        # if name in ONE_OR_NONE:
        #     # 不使用企鹅数据验证规则进行验证
        #     exclude_from_validation.append(itemrecord)
        #     if qty != 1:
        #         raise ValueError('%sx%d' % (name, qty))

        # 加入汇报列表
        yield itemrecord
