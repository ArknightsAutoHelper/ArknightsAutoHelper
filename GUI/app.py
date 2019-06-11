# system package import
import wx
import wx.grid
import time
# GUI package import
from GUI.Frames import *
# Ark package import
from Arknights.base import ArknightsHelper
from Arknights.click_location import LIZHI_CONSUME
# MISC package import
from collections import OrderedDict


class ArknightsAutoHelperGUI(wx.App):
    def __init__(self):
        self.Index = None
        self.worker = None
        wx.App.__init__(self)
        self.ark = None

        self.__current_active_frame = "Index"
        # load settings
        #
        # loaded
        self.backend_start_ark()
        self.backend_buffer_push()

    def __start_ark(self):
        try:
            self.ark = ArknightsHelper(call_by_gui=True, out_put=1)
        except Exception as e:
            self.Index.out_put_ctrl.AppendText(e)

    def __restart_ark(self):
        if self.ark is None:
            try:
                self.ark = ArknightsHelper(call_by_gui=True, out_put=1)
            except Exception as e:
                self.Index.out_put_ctrl.AppendText(e)
        else:
            self.ark.destroy()
            try:
                self.ark = ArknightsHelper(call_by_gui=True, out_put=1)
            except Exception as e:
                self.Index.out_put_ctrl.AppendText(e)

    def backend_start_ark(self):
        self.__start_ark()

    def backend_buffer_push(self):
        buffer = self.ark.shell_color.get_buffer()
        if buffer != "":
            self.Index.out_put_ctrl.AppendText(buffer)
        self.Index.current_lizhi.SetValue(self.ark.CURRENT_STRENGTH.__str__())
        wx.CallLater(500, self.backend_buffer_push)

    def OnInit(self):
        # Init All frames
        self.Index = Index(parent=None)
        # Init Router
        self.__bind_router()
        self.__bind_event()
        self.worker = None
        # Show Index
        self.Index.Show(show=True)
        return True

    def __bind_event(self):
        self.Index.test_ocr.Bind(wx.EVT_BUTTON, self.check_ocr_active)
        self.Index.main_start.Bind(wx.EVT_BUTTON, self.start_main)
        self.Index.slim_start.Bind(wx.EVT_BUTTON, self.start_slim)

    def check_ocr_active(self, event):
        event.Skip()

    def start_main(self, event):
        TASK_LIST = OrderedDict()
        if self.Index.task1_battle_name.GetValue() != "":
            TASK_LIST[self.Index.task1_battle_name.GetValue()] = int(self.Index.task1_battle_time.GetValue())
        if self.Index.task2_battle_name.GetValue() != "":
            TASK_LIST[self.Index.task2_battle_name.GetValue()] = int(self.Index.task2_battle_time.GetValue())
        if self.Index.task3_battle_name.GetValue() != "":
            TASK_LIST[self.Index.task3_battle_name.GetValue()] = int(self.Index.task3_battle_time.GetValue())
        if self.Index.task4_battle_name.GetValue() != "":
            TASK_LIST[self.Index.task4_battle_name.GetValue()] = int(self.Index.task4_battle_time.GetValue())
        for _ in TASK_LIST.keys():
            if _ not in LIZHI_CONSUME or "GT" in _:
                MessageDialog_OK("{} 不在支持的关卡列表中".format(_), "警告")
                return False

        if TASK_LIST.__len__() == 0:
            MessageDialog_CANCEL("未选择关卡", "提示")
            return False
        else:
            self.worker = ArkThread(ark=self.ark, TASK_LIST=TASK_LIST)

    def start_slim(self, event):
        c_id = self.Index.slim_battle_name.GetValue()
        set_count = int(self.Index.slim_battle_time.GetValue())
        self.worker = ArkThread(ark=self.ark, c_id=c_id, set_count=set_count)

    def __bind_router(self):
        pass

    def OnRouter_change(self, event, value='Index'):
        pass


def start_app():
    ArknightsAutoHelperGUI().MainLoop()
    wx.Exit()
