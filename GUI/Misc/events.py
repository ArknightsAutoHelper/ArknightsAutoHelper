import wx
import threading
import time
import inspect
import ctypes
from threading import Thread


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


class ArkThread(Thread):
    def __init__(self, ark, **param):
        '''
        我很少写进程处理的，有些问题还请多多包涵
        '''
        Thread.__init__(self)
        self.ark = ark
        if "func" in param:
            self.func = param['func']
        else:
            self.func = None
        if "c_id" in param:
            self.c_id = param['c_id']
        else:
            self.c_id = None
        if "set_count" in param:
            self.set_count = int(param['set_count'])
        else:
            self.set_count = None
        if "TASK_LIST" in param:
            self.TASK_LIST = param['TASK_LIST']
        else:
            self.TASK_LIST = None
        self.thread_type = ""
        self.start()

    def run(self):
        """Run Worker Thread."""
        if self.func is None:
            if self.TASK_LIST is not None:
                self.thread_type = "main_battle"
                self.ark.main_handler(self.TASK_LIST)
            else:
                self.thread_type = "slim_battle"
                self.ark.module_battle_slim(
                    c_id=self.c_id, set_count=self.set_count, set_ai=False,
                    self_fix=self.ark.ocr_active, sub=True
                )
        elif self.func == "login":
            self.thread_type = "login"
            self.ark.module_login()
        self.ark.shell_color.helper_text("{} 模块执行完毕".format(self.thread_type))
