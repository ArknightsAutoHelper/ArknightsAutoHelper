'''
[i] info_text
[+] helper_text
[!] warning_text
[X] failure_text
plain_text
'''
from Arknights.flags import *

class ShellColor(object):
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

    def warning_text(self, string):
        print(self.H_WARNING + string + self.E_END)

    def info_text(self, string):
        print(self.H_OK_BLUE + string + self.E_END)

    def failure_text(self, string):
        print(self.H_FAIL + string + self.E_END)

    def helper_text(self, string):
        print(self.H_OK_GREEN + string + self.E_END)

    def debug_text(self, string, level = 1):
        if DEBUG_LEVEL >= level:
            print(self.H_DEBUG + string + self.E_END)

    def plain_text(self, string):
        print(string)

    def run_test(self, string="[*] DEBUG COLOR"):
        self.warning_text(string)
        self.info_text(string)
        self.failure_text(string)
        self.helper_text(string)


class BufferColor(object):
    def __init__(self):
        self.H_HEADER = ''
        self.H_OK_BLUE = ' [i] '
        self.H_OK_GREEN = ' [+] '
        self.H_WARNING = ' [!] '
        self.H_FAIL = ' [X] '
        self.H_DEBUG = ' [D] '
        self.E_END = ''
        self.E_BOLD = ''
        self.E_UNDERLINE = ''
        self.__buffer = ""

    def warning_text(self, string):
        self.__buffer += self.H_WARNING + string + self.E_END + "\n"
        return self.__buffer

    def info_text(self, string):
        self.__buffer += self.H_OK_BLUE + string + self.E_END + "\n"
        return self.__buffer

    def failure_text(self, string):
        self.__buffer += self.H_FAIL + string + self.E_END + "\n"
        return self.__buffer

    def helper_text(self, string):
        self.__buffer += self.H_OK_GREEN + string + self.E_END + "\n"
        return self.__buffer

    def debug_text(self, string):
        self.__buffer += self.H_DEBUG + string + self.E_END + "\n"
        return self.__buffer

    def run_test(self, string="[*] DEBUG COLOR"):
        self.warning_text(string)
        self.info_text(string)
        self.failure_text(string)
        self.helper_text(string)

    def get_buffer(self):
        if self.__buffer != "":
            t = self.__buffer
            self.__buffer = ""
            return t
        else:
            return ""

    def clear_buffer(self):
        self.__buffer = ""
