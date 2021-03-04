# 为了自己用的爽，决定写一个命令行操作的交互式Shell帮助大家启动
# optparse 使用方法
# parser.add_option("-s", "--module-battle-slim",
# action="store_false",
# type=""
# dest="" 重命名字段
# default=False,
# help="make lots of noise [default]")

import optparse
from collections import OrderedDict

from Arknights.helper import ArknightsHelper
from Arknights.click_location import MAIN_TASK_SUPPORT


class ArknightsShell():
    def __init__(self):
        self.H_HEADER = '\033[95m'
        self.H_OK_BLUE = '\033[94m [i] '
        self.H_OK_GREEN = '\033[96m [+] '
        self.H_WARNING = '\033[93m [!] '
        self.H_FAIL = '\033[31m [X] '
        self.H_DEBUG = ' [D] '
        self.E_END = '\033[0m'
        self.E_BOLD = '\033[1m'
        self.E_UNDERLINE = '\033[4m'
        self.options = optparse.Values()
        self.task_list = OrderedDict()

    def run_shell(self):
        self.parser()
        self.handler()

    def parser(self):
        '''
        :return:
        '''
        usage = 'Usage: %prog [options] arg1 arg2 ...'
        parser = optparse.OptionParser(usage, version='%prog 1.0')
        parser.add_option("-s", "--module-battle-slim", dest="module_battle_slim",
                          action="store_true", default=False,
                          help="Module Battle Slim Option.\n Ensure the page is correct ")
        parser.add_option("-b", "--module-battle", dest="module_battle",
                          action="store_true", default=False,
                          help="Module Battle Option."
                          )
        parser.add_option("-t", "--task-list", type="string", default="", dest="task_list",
                          action="store", help="Input the TASK-LIST like string format 'CE-5:999|OF-8:10'\n"
                                               "Use : to split the battle_id and time \n Use | to split the task-list")
        parser.add_option("-c", "--clear-daily", action="store_true", default=False, dest="clear_daily",
                          help="Clear daily task if call this option")
        parser.add_option("-r", "--get-credit", action="store_true", default=False, dest="get_credit",
                          help="Get credit if call this option")
        parser.add_option("-u", "--get-building", action="store_true", default=False, dest="get_building",
                          help="Clear building if call this option")
        (self.options, _) = parser.parse_args()

        if self.options.module_battle_slim & self.options.module_battle:
            parser.error(
                self.E_BOLD + "[!] Cannot run scripts in both slim and full mode" + self.E_END
            )
        if self.options.task_list != "":
            self.__valid_TASK_LIST(task_list=self.options.task_list)

    def __valid_TASK_LIST(self, task_list):
        try:
            for x in task_list.split("|"):
                if x.split(":")[0] not in MAIN_TASK_SUPPORT:
                    raise Exception(
                        self.E_BOLD + "'{}' not in main task support list. \n"
                                      " Please change task name or use a same strength consume task if using slim mode".format(
                            x.split(":")[0]) + self.E_END
                    )
                self.task_list[x.split(":")[0]] = int(x.split(":")[1])

        except Exception as e:
            print(self.E_BOLD + e.__str__() + self.E_END)
            exit(0)

    def handler(self):
        if self.options.module_battle_slim | self.options.module_battle | self.options.clear_daily | self.options.get_credit | self.options.get_building:
            Ark = ArknightsHelper()
            if self.options.module_battle_slim:
                id, count = self.task_list.popitem()
                Ark.module_battle_slim(
                    c_id=None,
                    set_count=count,
                )

            if self.options.module_battle:
                Ark.main_handler(
                    clear_tasks=True,
                    task_list=self.task_list.items()
                )
            if self.options.clear_daily:
                Ark.clear_task()
                
            if self.options.get_credit:
                Ark.get_credit()
                
            if self.options.get_building:
                Ark.get_building()
