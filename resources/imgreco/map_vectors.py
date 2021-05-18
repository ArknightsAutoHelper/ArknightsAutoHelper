import numpy
from typing import Dict, List

stage_maps = {}
map_anchors = {}
ep2region: Dict[int, int] = {}
region2ep: Dict[int, List[int]] = {}
stage_maps_linear: Dict[str, List[str]] = {}
_invalid_stages = []

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
    episodes['ep08'] = episodes['ep07'] + vec(497, 0)
    stage_maps['episodes'] = episodes
    map_anchors['episodes'] = ['ep00', 'ep02', 'ep04', 'ep06', 'ep07']


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
        stage_maps_linear[prefix] = stage_maps[prefix].keys()

    # socs
    for infix in 'ABCD':
        map_anchors['PR-' + infix] = ['PR-%s-1' % infix]
        stage_maps_linear['PR-%s' % infix] = ['PR-%s-1' % infix, 'PR-%s-2' % infix]
    vec0 = vec(0, 0)
    stage_maps['PR-A'] = {'PR-A-1': vec0, 'PR-A-2': vec(401, -188)}
    stage_maps['PR-B'] = {'PR-B-1': vec0, 'PR-B-2': vec(456, -197)}
    stage_maps['PR-C'] = {'PR-C-1': vec0, 'PR-C-2': vec(445, -154)}
    stage_maps['PR-D'] = {'PR-D-1': vec0, 'PR-D-2': vec(426, -173)}

    stage_maps_linear['ep00'] = ['0-1', 'TR-1', '0-2', 'TR-2', '0-3', 'TR-3', '0-4', 'TR-4', '0-5', '0-6', 'TR-5',
                                 '0-7', 'TR-6', '0-8', '0-9', 'TR-7', '0-10', '0-11']
    stage_maps_linear['ep01'] = ['1-1', '1-2', '1-3', '1-4', '1-5', 'TR-8', '1-6', 'TR-9', '1-7', '1-8', 'TR-10',
                                 '1-9', '1-10', '1-11', '1-12']
    stage_maps_linear['ep02'] = ['TR-11', '2-1', 'S2-1', '2-2', 'S2-2', 'S2-3', 'S2-4', '2-3', 'TR-12', '2-4', 'S2-5',
                                 'S2-6', 'S2-7', 'TR-13', '2-5', '2-6', 'TR-14', '2-7', 'S2-8', 'S2-9', '2-8', '2-9',
                                 'S2-10', 'S2-11', 'S2-12', '2-10']
    stage_maps_linear['ep03'] = ['3-1', '3-2', '3-3', 'TR-15', 'S3-1', 'S3-2', '3-4', '3-5', '3-6', '3-7', 'S3-3',
                                 '3-8', 'S3-4', 'S3-5', 'S3-6', 'S3-7']
    stage_maps_linear['ep04'] = ['4-1', '4-2', '4-3', 'S4-1', 'S4-2', 'S4-3', '4-4', '4-5', '4-6', 'S4-4', 'S4-5',
                                 'S4-6', '4-7', '4-8', '4-9', 'S4-7', 'S4-8', 'S4-9', 'S4-10', '4-10']
    stage_maps_linear['ep05'] = ['5-1', '5-2', 'S5-1', '5-3', '5-4', '5-5', '5-6', 'S5-3', 'S5-4', '5-7', '5-8', '5-9',
                                 'S5-5', 'S5-6', 'S5-7', 'S5-8', '5-10', 'S5-9']
    stage_maps_linear['ep06'] = ['6-1', '6-2', '6-3', '6-4', '6-5', '6-6', '6-7', '6-8', 'TR-16', '6-9', '6-10', 'S6-1',
                                 'S6-2', '6-11', '6-12', '6-13', '6-14', '6-15', 'S6-3', 'S6-4', '6-16', '6-17', '6-18',
                                 'H6-1', 'H6-4']
    stage_maps_linear['ep07'] = ['7-1', '7-2', '7-3', '7-4', '7-5', 'TR-17', '7-6', '7-7', '7-8', '7-9', '7-10', '7-11',
                                 '7-12', '7-13', '7-14', '7-15', '7-16', 'S7-1', 'S7-2', '7-17', '7-18', '7-19', '7-20']
    stage_maps_linear['ep08'] = ['R8-1', 'M8-1', 'TR-18', 'R8-2', 'M8-2', 'R8-3', 'M8-3', 'R8-4', 'M8-4', 'R8-5',
                                 'M8-5', 'R8-6', 'R8-7', 'R8-8', 'EG-1', 'M8-6', 'EG-2', 'R8-9', 'M8-7', 'R8-10',
                                 'R8-11', 'M8-8', 'EG-3', 'JT8-1', 'JT8-2', 'JT8-3', 'EG-4', 'END8-1', 'EG-5']

    global _invalid_stages
    _invalid_stages = ['1-2', '1-11', '5-11', '6-13', '6-17', '6-18', '7-1', '7-7', '7-19', '7-20', 'M8-1', 'M8-2',
                       'M8-3', 'M8-4', 'M8-5', 'EG-1', 'EG-2', 'EG-3', 'JT8-1', 'EG-4', 'END8-1', 'EG-5',
                       'H6-1', 'H6-4']
    tmp = []
    for i in range(4):
        ep2region[i] = 0
        tmp.append(i)
    region2ep[0] = tmp
    tmp = []
    for i in range(4, 9):
        ep2region[i] = 1
        tmp.append(i)
    region2ep[1] = tmp


def is_invalid_stage(stage):
    if stage.startswith('TR-'):
        return True
    return stage in _invalid_stages


initialize()
