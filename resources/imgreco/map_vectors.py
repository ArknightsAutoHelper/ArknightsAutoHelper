import numpy

stage_maps = {}
map_anchors = {}


def vec(*scalars, dtype=numpy.int32):
    return numpy.array(scalars, dtype=dtype)


"""
关卡定位说明：
此处记录 720 渲染高度，宽高比大于 16:9（如 1280x720、1440x720）下的各个关卡的相对坐标。
所有随拖动同步运动的关卡图标组成一个 partition，partition 中的坐标以参考点+向量形式表示，
一个 partition 中有数个定位用锚点（anchor）。

stage_maps[partition] 为 partition 内名称到相对坐标的 Mapping
map_anchors[partition] 为该 partition 内锚点的名称的列表

锚点（anchor）选取规则：
在 16:9 宽高比下，始终有一个锚点在可视区域内。
"""


def initialize():
    # partition "episodes"
    episodes = {}
    episodes['ep00'] = vec(0, 0)
    episodes['ep01'] = episodes['ep00'] + vec(497, 0)
    episodes['ep02'] = episodes['ep01'] + vec(497, 0)
    episodes['ep03'] = episodes['ep02'] + vec(497, 0)
    episodes['ep04'] = episodes['ep03'] + vec(497, 0)
    episodes['ep05'] = episodes['ep04'] + vec(497, 0)
    episodes['ep06'] = episodes['ep05'] + vec(497, 0)
    episodes['ep07'] = episodes['ep06'] + vec(497, 0)
    stage_maps['episodes'] = episodes
    map_anchors['episodes'] = list(episodes.keys())


    # partition "ep01"
    ep01 = {}
    ep01['1-1'] = vec(0, 0)
    ep01['1-5'] = ep01['1-1'] + vec(1067, 105)
    ep01['1-7'] = ep01['1-5'] + vec(982, -226)
    ep01['1-10'] = ep01['1-7'] + vec(1041, 232)
    stage_maps['ep01'] = ep01
    map_anchors['ep01'] = ['1-1', '1-5', '1-7', '1-10']


    # partition "ep04"
    ep04 = {}
    ep04['4-1'] = vec(0, 0)  # anchor
    ep04['4-2'] = ep04['4-1'] + vec(206, 109)
    ep04['4-3'] = ep04['4-1'] + vec(394, 0)
    ep04['S4-1'] = ep04['4-1'] + vec(601, 109)
    ep04['S4-2'] = ep04['4-1'] + vec(807, 191)
    ep04['S4-3'] = ep04['4-1'] + vec(1012, 109)
    ep04['4-4'] = ep04['4-1'] + vec(1224, 0)  # anchor
    ep04['4-5'] = ep04['4-4'] + vec(221, -90)
    ep04['4-6'] = ep04['4-4'] + vec(445, 0)  # anchor
    ep04['S4-4'] = ep04['4-4'] + vec(633, 90)
    ep04['S4-5'] = ep04['4-4'] + vec(914, 90)
    ep04['S4-6'] = ep04['4-4'] + vec(1196, 90)
    ep04['4-7'] = ep04['S4-6'] + vec(201, -90)  # anchor
    ep04['4-8'] = ep04['S4-6'] + vec(419, -180)
    ep04['4-9'] = ep04['S4-6'] + vec(624, -90)
    ep04['S4-7'] = ep04['S4-6'] + vec(831, -276)  # anchor
    ep04['S4-8'] = ep04['S4-6'] + vec(1051, -186)
    ep04['S4-9'] = ep04['S4-6'] + vec(1319, -186)
    ep04['S4-10'] = ep04['S4-9'] + vec(268, 0)
    ep04['4-10'] = ep04['S4-9'] + vec(521, 96)  # anchor
    stage_maps['ep04'] = ep04
    map_anchors['ep04'] = ['4-1', '4-4', '4-6', '4-7', 'S4-7', '4-10']


    # materials
    material1 = vec(0, 0)
    material2 = material1 + vec(277, -50)
    material3 = material1 + vec(477, -165)
    material4 = material1 + vec(643, -279)
    material5 = material1 + vec(743, -394)
    for prefix in ['LS', 'AP', 'CA', 'CE', 'SK']:
        stage_maps[prefix] = {prefix + '-1': material1, prefix + '-2': material2, prefix + '-3': material3,
                              prefix + '-4': material4, prefix + '-5': material5}
        map_anchors[prefix] = [prefix + '-1']

    # socs
    for infix in 'ABCD':
        map_anchors['PR-' + infix] = ['PR-%s-1' % infix]
    vec0 = vec(0, 0)
    stage_maps['PR-A'] = {'PR-A-1': vec0, 'PR-A-2': vec(401, -188)}
    stage_maps['PR-B'] = {'PR-B-1': vec0, 'PR-B-2': vec(456, -197)}
    stage_maps['PR-C'] = {'PR-C-1': vec0, 'PR-C-2': vec(445, -154)}
    stage_maps['PR-D'] = {'PR-D-1': vec0, 'PR-D-2': vec(426, -173)}


initialize()
