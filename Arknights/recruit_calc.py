import itertools
import sys

from .recruit_database import recruit_database


def _rank(operators):
    if any(x[1] == 2 for x in operators):  # 组合中有三星干员
        return 0
    min_rarity = min(x[1] for x in operators if x[1] > 0)  # 一星干员不参与评级
    return min_rarity - 2


def calculate(tags):
    tags = sorted(tags)
    operator_for_tags = {}
    for tag in tags:
        if tag == '高级资深干员':
            operator_for_tags[(tag,)] = [x[:2] for x in recruit_database if x[1] == 5]
        elif tag == '资深干员':
            operator_for_tags[(tag,)] = [x[:2] for x in recruit_database if x[1] == 4]
        else:
            operators = [x[:2] for x in recruit_database if tag in x[2]]
            if len(operators) == 0:
                raise ValueError('未知 tag: ' + tag)
            operator_for_tags[(tag,)] = operators

    for comb2 in itertools.combinations(tags, 2):
        set1 = operator_for_tags[(comb2[0],)]
        set2 = set(operator_for_tags[(comb2[1],)])
        operators = [x for x in set1 if x in set2]
        if len(operators):
            operator_for_tags[comb2] = operators

    for comb3 in itertools.combinations(tags, 3):
        set1 = operator_for_tags[(comb3[0],)]
        set2 = operator_for_tags[(comb3[1],)]
        set3 = set(operator_for_tags[(comb3[2],)])

        operators = [x for x in set1 if x in set2]
        operators = [x for x in operators if x in set3]

        if len(operators):
            operator_for_tags[comb3] = operators

    for tags in operator_for_tags:
        ops = list(operator_for_tags[tags])
        if '高级资深干员' not in tags:
            ops = [op for op in ops if op[1] != 5]
        ops.sort(key=lambda x: x[1], reverse=True)
        operator_for_tags[tags] = ops
    items = list(operator_for_tags.items())
    combs = [(tags, ops, _rank(ops)) for tags, ops in items]
    return sorted(combs, key=lambda x: x[2], reverse=True)


if __name__ == '__main__':
    import pprint
    pprint.pprint(calculate(sys.argv[1:]))
