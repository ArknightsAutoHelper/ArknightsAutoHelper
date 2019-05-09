from collections import OrderedDict

SMALL_WAIT = 3
MEDIUM_WAIT = 5
BIG_WAIT = 10
SECURITY_WAIT = 15
BATTLE_FINISH_DETECT = 30

CLICK_LOCATION = {
    # 开始页面点击 QS 位置
    'MAIN_RETURN_INDEX': (16, 62),
    "LOGIN_QUICK_LOGIN": (640, 675),
    "LOGIN_START_WAKEUP": (642, 507),
    "BATTLE_CLICK_IN": (1173, 186),
    'BATTLE_CLICK_AI_COMMANDER': (1109, 588),
    'BATTLE_CLICK_START_BATTLE': (1137, 658),
    'BATTLE_CLICK_ENSURE_TEAM_INFO': (1094, 613),

    "BATTLE_SELECT_MAIN_TASK": (75, 663),
    "BATTLE_SELECT_MAIN_TASK_2": (1213, 311),
    "BATTLE_SELECT_MAIN_TASK_2-2": (1265, 338),
    "BATTLE_SELECT_MAIN_TASK_S2-1": (1054, 431),
    # "BATTLE_SELECT_MAIN_TASK_Chapter1": (153, 346),
    # "BATTLE_SELECT_MAIN_TASK_Chapter2": (657, 366),
    # "BATTLE_SELECT_MAIN_TASK_2-2": (881, 346),
    # "BATTLE_SELECT_MAIN_TASK_2-1": (622, 345),

    "BATTLE_SELECT_MATERIAL_COLLECTION": (236, 658),
    # 预定义部分
    "BATTLE_SELECT_MATERIAL_COLLECTION_0": (168, 375),
    "BATTLE_SELECT_MATERIAL_COLLECTION_1": (452, 375),
    "BATTLE_SELECT_MATERIAL_COLLECTION_2": (739, 375),
    "BATTLE_SELECT_MATERIAL_COLLECTION_X-1": (135, 570),
    "BATTLE_SELECT_MATERIAL_COLLECTION_X-2": (135, 570),
    "BATTLE_SELECT_MATERIAL_COLLECTION_X-3": (664, 402),
    "BATTLE_SELECT_MATERIAL_COLLECTION_X-4": (778, 293),
    "BATTLE_SELECT_MATERIAL_COLLECTION_X-5": (880, 167),
    # COLLECTION NOT FINISH
    "BATTLE_SELECT_MATERIAL_COLLECTION_CE": (998, 384),
    "BATTLE_SELECT_MATERIAL_COLLECTION_CE-3": (664, 402),
    "BATTLE_SELECT_MATERIAL_COLLECTION_CE-4": (776, 284),
    # SK
    "BATTLE_SELECT_MATERIAL_COLLECTION_SK": (745, 384),  # 3 LOCATION
    "BATTLE_SELECT_MATERIAL_COLLECTION_SK-3": (664, 402),

    "BATTLE_SELECT_CHIP_SEARCH": (387, 658),
    # 预定义部分
    "BATTLE_SELECT_CHIP_SEARCH_PR-2": (503, 414),
    "BATTLE_SELECT_CHIP_SEARCH_PR-X-1": (324, 415),
    "BATTLE_SELECT_CHIP_SEARCH_PR-X-2": (767, 251),
    # 实际部分方便操作
    "BATTLE_SELECT_CHIP_SEARCH_PR-A": (248, 456),
    "BATTLE_SELECT_CHIP_SEARCH_PR-A-1": (452, 432),
    "BATTLE_SELECT_CHIP_SEARCH_PR-C": (478, 412),
    "BATTLE_SELECT_CHIP_SEARCH_PR-C-1": (324, 415),
    "BATTLE_SELECT_CHIP_SEARCH_PR-C-2": (767, 251)
}

MAIN_TASK_LOCATION = {
    "2-2": (1, 1),
    "2-1": (1, 1)
}

MAP_LOCATION = {
    # 截图位置 # （X,Y） (DX,DY)
    "BATTLE_CLICK_AI_COMMANDER": ((1055, 580), (23, 23)),
    "BATTLE_INFO_BATTLE_END": ((30, 573), (375, 100)),
    "BATTLE_INFO_STRENGTH_REMAIN": ((1128, 21), (128, 33))
}

SWIPE_LOCATION = {
    # 拖动动作 # (X1,Y1) -> (X2,Y2)
    "BATTLE_TO_MAP_LEFT": ((24, 87), (1200, 0)),
    "BATTLE_TO_MAP_RIGHT": ((1271, 157), (10, 157))
}

LIZHI_CONSUME = {
    # 理智消耗 c_id : number
    'CE-3': 20,
    'CE-2': 15,
    'CE-1': 10,
    'CE-4': 25,
    'CE-5': 30,
    'LS-5': 30,
    'SK-3': 20,
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
    "S2-1": 9,
    "2-2": 9
}

BATTLE_SELECTORS = {
    1: 'MAIN_TASK',  # 主线任务
    2: 'MATERIAL_COLLECTION',  # 物资筹备
    3: 'CHIP_SEARCH',  # 芯片收集
    4: 'EXTERMINATE_BATTLE'
}

DAILY_LIST = {
    # 日常位置定位
    # 键值表示 BATTLE_SELECTORS
    3: {
        # __import__('datetime').datetime.now().strftime("%w")
        '4':
            {
                'A': 1,
                'C': 2,
            }
    },
    2: {
        # __import__('datetime').datetime.now().strftime("%w")
        '1':
            {
                'LS': 0,
            },
        '2':
            {
                'LS': 0,
            },
        '3':
            {
                'LS': 0,
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
            },
        '6':
            {
                'LS': 0,
            },
        '7':
            {
                'LS': 0,
            },
    }
}
