from Arknights import ArknightsHelper
from collections import OrderedDict
TASK_LIST = OrderedDict()
TASK_LIST['CE-5'] = 2
TASK_LIST['LS-5'] = 1
Ark = ArknightsHelper()
Ark.main_handler(TASK_LIST)
# Ark.module_battle(c_id='CE-5', set_count=5)

# Ark.module_battle_slim(c_id='CE-5', set_count=10, set_ai=True)
