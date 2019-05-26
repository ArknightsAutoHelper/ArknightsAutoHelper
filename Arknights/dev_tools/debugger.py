from Arknights.base import ArknightsHelper
from Arknights.click_location import *

c_id = "CE-5"
mode = 2
self = ArknightsHelper()
print(self.selector.get_week())
X = DAILY_LIST[mode][self.selector.get_week()][c_id[0:2]]
