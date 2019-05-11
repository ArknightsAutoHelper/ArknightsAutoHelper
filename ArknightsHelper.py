from Arknights import ArknightsHelper
from collections import OrderedDict

TASK_LIST = OrderedDict()
# TASK_LIST["S2-1"] = 2
# TASK_LIST['2-2'] = 10
# TASK_LIST["LS-5"] = 5
TASK_LIST["CE-5"] = 5
Ark = ArknightsHelper()
Ark.main_handler(TASK_LIST)
