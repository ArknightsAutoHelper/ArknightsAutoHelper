from collections import OrderedDict

CLICK_LOCATION = {
    # 开始页面点击 QS 位置
    'CENTER_CLICK': (350, 230),
    'MAIN_RETURN_INDEX': (16, 62),
    "LOGIN_QUICK_LOGIN": (640, 675),
    "LOGIN_START_WAKEUP": (642, 507),
    "BATTLE_CLICK_IN": (1173, 186),
    'BATTLE_CLICK_AI_COMMANDER': (1109, 588),
    'BATTLE_CLICK_START_BATTLE': (1151, 658),
    'BATTLE_CLICK_ENSURE_TEAM_INFO': (1104, 512),

    "BATTLE_SELECT_MAIN_TASK": (75, 663),
    "BATTLE_SELECT_MAIN_TASK_2": (1213, 311),
    "BATTLE_SELECT_MAIN_TASK_4": (969, 362),

    "BATTLE_SELECT_MAIN_TASK_2-2": (1265, 338),
    "BATTLE_SELECT_MAIN_TASK_S2-1": (1054, 431),
    "BATTLE_SELECT_MAIN_TASK_4-4": (610, 339),
    "BATTLE_SELECT_MAIN_TASK_4-5": (824, 254),
    "BATTLE_SELECT_MAIN_TASK_4-6": (1034, 340),
    "BATTLE_SELECT_MAIN_TASK_4-7": (771, 343),

    "BATTLE_SELECT_MATERIAL_COLLECTION": (236, 658),
    # 预定义部分
    "BATTLE_SELECT_MATERIAL_COLLECTION_0": (168, 375),
    "BATTLE_SELECT_MATERIAL_COLLECTION_1": (452, 375),
    "BATTLE_SELECT_MATERIAL_COLLECTION_2": (739, 375),
    "BATTLE_SELECT_MATERIAL_COLLECTION_3": (1005, 356),
    "BATTLE_SELECT_MATERIAL_COLLECTION_X-1": (135, 570),
    "BATTLE_SELECT_MATERIAL_COLLECTION_X-2": (135, 570),
    "BATTLE_SELECT_MATERIAL_COLLECTION_X-3": (664, 402),
    "BATTLE_SELECT_MATERIAL_COLLECTION_X-4": (778, 293),
    "BATTLE_SELECT_MATERIAL_COLLECTION_X-5": (880, 167),

    "BATTLE_SELECT_CHIP_SEARCH": (387, 658),
    # 预定义部分
    "BATTLE_SELECT_CHIP_SEARCH_PR-1": (264, 367),
    "BATTLE_SELECT_CHIP_SEARCH_PR-2": (503, 414),
    "BATTLE_SELECT_CHIP_SEARCH_PR-3": (762, 396),
    "BATTLE_SELECT_CHIP_SEARCH_PR-X-1": (324, 415),
    "BATTLE_SELECT_CHIP_SEARCH_PR-X-2": (767, 251),
}
#
# MAIN_TASK_LOCATION = {
#     "2-2": (1, 1),
#     "2-1": (1, 1)
# }

MAP_LOCATION = {
    # 截图位置 # （X,Y） (DX,DY)
    "BATTLE_CLICK_AI_COMMANDER": ((1055, 580), (23, 23)),
    "BATTLE_INFO_BATTLE_END": ((30, 573), (375, 100)),
    "BATTLE_INFO_STRENGTH_REMAIN": ((1128, 21), (152, 33)),
    "BATTLE_INFO_LEVEL_UP": ((288, 348), (184, 58)),
    "BATTLE_INFO_LEVEL_UP_BLACK": ((827, 244), (136, 67)),
    "BATTLE_INFO_EAT_STONE": ((880, 520), (113, 37)),
}

SWIPE_LOCATION = {
    # 拖动动作 # (X1,Y1) -> (X2,Y2)
    "BATTLE_TO_MAP_LEFT": ((24, 87), (1200, 0)),
    "BATTLE_TO_MAP_RIGHT": ((1023, 157), (-600, 0))
}

LIZHI_CONSUME = {
    # 理智消耗 c_id : number
    # CA
    'CA-1': 10,
    'CA-2': 15,
    'CA-3': 20,
    'CA-4': 25,
    'CA-5': 30,
    # CE
    'CE-3': 20,
    'CE-2': 15,
    'CE-1': 10,
    'CE-4': 25,
    'CE-5': 30,
    # LS
    'LS-1': 10,
    'LS-2': 15,
    'LS-3': 20,
    'LS-4': 25,
    'LS-5': 30,
    # SK
    'SK-1': 10,
    'SK-2': 15,
    'SK-3': 20,
    'SK-4': 25,
    'SK-5': 30,
    # AP
    'AP-1': 10,
    'AP-2': 15,
    'AP-3': 20,
    'AP-4': 25,
    'AP-5': 30,
    # PR
    'PR-A-1': 18,
    'PR-A-2': 36,
    'PR-B-1': 18,
    'PR-B-2': 36,
    'PR-C-1': 18,
    'PR-C-2': 36,
    'PR-D-1': 18,
    'PR-D-2': 36,
    # 主关卡
    # 关于主关卡的选关部分还没有充分测试，目前支持的关卡如下所示
    "S2-1": 9,
    "2-2": 9,
    '4-4': 18,
    '4-5': 18,
    '4-6': 18,
    '4-7': 18,
    # 以下是不支持的关卡，但是可以通过简略战斗模块启动
    '3-8': 18,
    "S2-12": 15,
    '4-8': 21,
    '4-9': 21,
    # 活动关卡
    # TASK_LIST 功能不支持活动关卡
    'GT-6': 15,
    'GT-5': 15,
    'GT-4': 12,
    'GT-3': 12,
    'GT-2': 9,
    'GT-1': 9,
}

BATTLE_SELECTORS = {
    1: 'MAIN_TASK',  # 主线任务
    2: 'MATERIAL_COLLECTION',  # 物资筹备
    3: 'CHIP_SEARCH',  # 芯片收集
    4: 'EXTERMINATE_BATTLE'
}

# 拖动次数
# 只更新一些需要刷素材的关卡
MAIN_TASK_CHAPTER_SWIPE = {
    # 1 代表 1次 BATTLE_TO_MAP_RIGHT
    '4': 1,
}

MAIN_TASK_BATTLE_SWIPE = {
    # 1 代表 1次 BATTLE_TO_MAP_RIGHT
    '4-4': 1,
    '4-5': 1,
    '4-6': 1,
    '4-7': 2,
    '4-8': 2,
}

MAIN_TASK_RELOCATE = {
    # 可能我们不需要这个
    "4-7": (494, 342),
}

DAILY_LIST = {
    # 日常位置定位
    # 数据来自于http://wiki.joyme.com/arknights/%E9%A6%96%E9%A1%B5
    # 顺序可能有问题
    3: {
        # __import__('datetime').datetime.now().strftime("%w")
        # 关卡名	开放时间	        掉落物资                关卡ID
        # 固若金汤	一、四、五、日	重装、医疗精英化材料     A
        # 摧枯拉朽	一、二、五、六	术师、狙击精英化材料     B
        # 势不可挡	三、四、六、日	先锋、辅助精英化材料     C
        # 身先士卒	二、三、六、日	近卫、特种精英化材料     D
        '1':
            {
                'A': 1,
                'B': 2,
            },
        '2':
            {
                'B': 1,
                'D': 2,
            },
        '3':
            {
                'C': 1,
                'D': 2,
            },
        '4':
            {
                'A': 1,
                'C': 2,
            },
        '5':
            {
                'A': 1,
                'B': 2,
            },
        '6':
            {
                'B': 1,
                'C': 2,
                'D': 3,
            },
        '7':
            {
                'A': 1,
                'C': 1,
                'D': 3,
            },
    },
    2: {
        # 关卡名	开放时间	        掉落物资       关卡ID
        # 战术演习	常驻开放        	作战记录       LS
        # 空中威胁	二、三、五、日	技巧概要       CA
        # 粉碎防御	一、四、六、日	采购凭证       AP
        # 资源保障	一、三、五、六	碳、家具零件   SK
        # 货物运送	二、四、六、日	龙门币         CE
        # __import__('datetime').datetime.now().strftime("%w")
        '1':
            {
                'LS': 0,
                'AP': 1,
                'SK': 2,
            },
        '2':
            {
                'LS': 0,
                'CA': 1,
                'CE': 2,
            },
        '3':
            {
                'LS': 0,
                'CA': 1,
                'SK': 2,
            },
        '4':
            {
                'LS': 0,
                'AP': 1,
                'CE': 2,
            },
        '5':
            {
                'LS': 0,
                'CA': 1,
                'SK': 2,
            },
        '6':
            {
                'LS': 0,
                'AP': 1,
                'SK': 2,
                'CE': 3,
            },
        '7':
            {
                'LS': 0,
                'AP': 1,
                'CA': 2,
                'CE': 3,
            },
    }
}
