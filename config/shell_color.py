class ShellColor(object):
    def __init__(self):
        self.H_HEADER = '\033[95m'
        self.H_OK_BLUE = '\033[94m'
        self.H_OK_GREEN = '\033[96m'
        self.H_WARNING = '\033[93m'
        self.H_FAIL = '\033[31m'
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

    def run_test(self, string="[*] DEBUG COLOR"):
        self.warning_text(string)
        self.info_text(string)
        self.failure_text(string)
        self.helper_text(string)


class BufferColor(object):
    def __init__(self):
        self.H_HEADER = '\033[95m'
        self.H_OK_BLUE = '\033[94m'
        self.H_OK_GREEN = '\033[96m'
        self.H_WARNING = '\033[93m'
        self.H_FAIL = '\033[31m'
        self.E_END = '\033[0m'
        self.E_BOLD = '\033[1m'
        self.E_UNDERLINE = '\033[4m'
        self.__buffer = ""
        self.__is_buffer_change = True

    def warning_text(self, string):
        self.__is_buffer_change = True
        self.__buffer = self.H_WARNING + string + self.E_END
        return self.__buffer

    def info_text(self, string):
        self.__is_buffer_change = True
        self.__buffer = self.H_OK_BLUE + string + self.E_END
        return self.__buffer

    def failure_text(self, string):
        self.__is_buffer_change = True
        self.__buffer = self.H_FAIL + string + self.E_END
        return self.__buffer

    def helper_text(self, string):
        self.__is_buffer_change = True
        self.__buffer = self.H_OK_GREEN + string + self.E_END
        return self.__buffer

    def run_test(self, string="[*] DEBUG COLOR"):
        self.warning_text(string)
        self.info_text(string)
        self.failure_text(string)
        self.helper_text(string)

    def get_buffer(self):
        if self.__is_buffer_change:
            self.__is_buffer_change = False
            return self.__buffer
        else:
            pass

    def clear_buffer(self):
        self.__buffer = ""
