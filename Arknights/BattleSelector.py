from datetime import datetime, timedelta


class BattleSelector(object):
    def __init__(self, id=None):
        self.battle_selectors = {
            1: 'MAIN_TASK',  # 主线任务
            2: 'MATERIAL_COLLECTION',  # 物资筹备
            3: 'CHIP_SEARCH',  # 芯片收集
            4: 'EXTERMINATE_BATTLE'
        }
        self.id = id

    def id_checker(self, id=None):
        if id is not None:
            self.id = id
        else:
            id = self.id
        if id[0].isnumeric() or (id[0] == "S" and id[1].isnumeric()):
            return 1
        elif id[0:2].upper() == "CE" or id[0:2].upper() == "SK" or id[0:2].upper() == "LS" or id[0:2].upper() == 'AP':
            return 2
        elif id[0:2].upper() == "PR":
            return 3
        # elif id[0].upper() == "E":
        #     return 4
        else:
            return False

    def get_id_swipe(self):
        pass

    @staticmethod
    def get_week():
        '''
        由于明日方舟的时间更新时间是从 4：00 AM 开始的所以我们把时区往前挪4个小时
        :return:
        '''
        return str((datetime.now() - timedelta(hours=4)).weekday())

# if __name__ == '__main__':
#     b = BattleSelector()
#     print(b.get_week())
