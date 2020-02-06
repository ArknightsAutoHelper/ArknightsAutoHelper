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

        # 移除空分组
        if len(group[1]) == 0:
            itemgroups.pop(j)

    return itemgroups
