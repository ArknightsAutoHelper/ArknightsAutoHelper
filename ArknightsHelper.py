from Arknights import ArknightsHelper
from collections import OrderedDict

TASK_LIST = OrderedDict()
# TASK_LIST['LS-4'] = 10
Ark = ArknightsHelper()
# Ark.main_handler(TASK_LIST)
Ark.module_battle_slim(c_id='CE-5', set_count=14, set_ai=True)
