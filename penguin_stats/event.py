import copy
from typing import Tuple, List


def event_preprocess(stage: str, itemgroups: List[Tuple[str, List[Tuple[str, int]]]], exclude_from_validation: List[Tuple[str, int]]):
    itemgroups = copy.deepcopy(itemgroups)
    for j, group in enumerate(itemgroups):
        items = group[1]
        for i, item in enumerate(items):

            if item[0] == '量子二踢脚':
                items.pop(i)  # 从汇报列表中移除
                continue

            if item[0] == '应急理智小样' or item[0] == '罗德岛物资补给':
                if item[1] != 1:
                    raise ValueError('%sx%d' % item)
                exclude_from_validation.append(item)
                continue

            # 活动时间：2月8日04:00 - 2月22日03:59
            if item[0] == '岁过华灯':
                if item[1] != 1:
                    raise ValueError('%sx%d' % item)
                exclude_from_validation.append(item)
                continue

            # 关卡开放时间：02月25日 16:00 - 03月3日 03:59 
            if item[0] == '食堂汤点券':
                items.pop(i)
                continue

            # 活动时间：04月21日 16:00 - 05月05日 03:59
            if item[0] == '无名的识别牌':
                items.pop(i)
                continue

            # 活动时间：05月15日 16:00 - 05月29日 03:59
            if item[0] == '32h战略配给':
                if item[1] != 1:
                    raise ValueError('%sx%d' % item)
                exclude_from_validation.append(item)
                continue

            # 关卡开放时间：06月18日 16:00 - 06月25日 03:59
            if item[0] == '彼得海姆热销饼干':
                items.pop(i)
                continue

        # 移除空分组
        if len(group[1]) == 0:
            itemgroups.pop(j)

    return itemgroups
