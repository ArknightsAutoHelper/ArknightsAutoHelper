from Arknights import ArknightsHelper
from collections import OrderedDict

TASK_LIST = OrderedDict()
# TASK_LIST["S2-1"] = 2
# TASK_LIST['2-2'] = 10
# TASK_LIST["4-6"] = 12
TASK_LIST["CE-5"] = 3
TASK_LIST["LS-5"] = 3
Ark = ArknightsHelper()
Ark.main_handler(TASK_LIST)
