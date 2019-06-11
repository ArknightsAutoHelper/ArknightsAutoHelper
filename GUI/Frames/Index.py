# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Jan  9 2019)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc


###########################################################################
## Class MyFrame1
###########################################################################

class Index(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title="Arknights Auto Helper GUI V0.1 beta By shaobaobaoer",
                          pos=wx.DefaultPosition,
                          size=wx.Size(835, 629), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INACTIVEBORDER))

        bSizer2 = wx.BoxSizer(wx.VERTICAL)

        bSizer2.Add((0, 20), 0, wx.EXPAND, 5)

        fgSizer2 = wx.FlexGridSizer(1, 3, 0, 0)
        fgSizer2.SetFlexibleDirection(wx.BOTH)
        fgSizer2.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.m_bitmap4 = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(u"GUI/Misc/kong.png", wx.BITMAP_TYPE_ANY),
                                         wx.DefaultPosition, wx.Size(200, 500), 0)
        fgSizer2.Add(self.m_bitmap4, 0, wx.ALL, 5)

        fgSizer3 = wx.FlexGridSizer(0, 3, 0, 0)
        fgSizer3.SetFlexibleDirection(wx.BOTH)
        fgSizer3.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.m_staticText41 = wx.StaticText(self, wx.ID_ANY, u"OCR探针", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText41.Wrap(-1)

        self.m_staticText41.SetFont(
            wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "黑体"))

        fgSizer3.Add(self.m_staticText41, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.m_staticText413 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText413.Wrap(-1)

        fgSizer3.Add(self.m_staticText413, 0, wx.ALL, 5)

        self.m_staticText414 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText414.Wrap(-1)

        fgSizer3.Add(self.m_staticText414, 0, wx.ALL, 5)

        self.test_ocr = wx.Button(self, wx.ID_ANY, u"测试", wx.DefaultPosition, wx.DefaultSize, 0)
        self.test_ocr.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.test_ocr, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.m_staticText57 = wx.StaticText(self, wx.ID_ANY, u"当前理智", wx.DefaultPosition, wx.Size(-1, -1), 0)
        self.m_staticText57.Wrap(-1)

        self.m_staticText57.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.m_staticText57, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.current_lizhi = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(50, -1), 0)
        fgSizer3.Add(self.current_lizhi, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_staticText27 = wx.StaticText(self, wx.ID_ANY, u"主战斗模块", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText27.Wrap(-1)

        self.m_staticText27.SetFont(
            wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "黑体"))

        fgSizer3.Add(self.m_staticText27, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_BOTTOM, 5)

        self.m_staticText418 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText418.Wrap(-1)

        fgSizer3.Add(self.m_staticText418, 0, wx.ALL, 5)

        self.m_staticText42 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(-1, 40), 0)
        self.m_staticText42.Wrap(-1)

        fgSizer3.Add(self.m_staticText42, 0, wx.ALL, 5)

        self.m_staticText43 = wx.StaticText(self, wx.ID_ANY, u"TASK1", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText43.Wrap(-1)

        self.m_staticText43.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.m_staticText43, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.task1_battle_name = wx.TextCtrl(self, wx.ID_ANY, u"GT-6", wx.DefaultPosition, wx.DefaultSize, 0)
        fgSizer3.Add(self.task1_battle_name, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.task1_battle_time = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                             wx.SP_ARROW_KEYS, 0, 100, 1)
        fgSizer3.Add(self.task1_battle_time, 0, wx.ALL | wx.EXPAND, 5)

        self.m_staticText431 = wx.StaticText(self, wx.ID_ANY, u"TASK2", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText431.Wrap(-1)

        self.m_staticText431.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.m_staticText431, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.task2_battle_name = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        fgSizer3.Add(self.task2_battle_name, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.task2_battle_time = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                             wx.SP_ARROW_KEYS, 0, 100, 1)
        fgSizer3.Add(self.task2_battle_time, 0, wx.ALL | wx.EXPAND, 5)

        self.m_staticText4311 = wx.StaticText(self, wx.ID_ANY, u"TASK3", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText4311.Wrap(-1)

        self.m_staticText4311.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.m_staticText4311, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.task3_battle_name = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        fgSizer3.Add(self.task3_battle_name, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.task3_battle_time = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                             wx.SP_ARROW_KEYS, 0, 100, 1)
        fgSizer3.Add(self.task3_battle_time, 0, wx.ALL | wx.EXPAND, 5)

        self.m_staticText43111 = wx.StaticText(self, wx.ID_ANY, u"TASK4", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText43111.Wrap(-1)

        self.m_staticText43111.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.m_staticText43111, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.task4_battle_name = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        fgSizer3.Add(self.task4_battle_name, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.task4_battle_time = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                             wx.SP_ARROW_KEYS, 0, 100, 1)
        fgSizer3.Add(self.task4_battle_time, 0, wx.ALL | wx.EXPAND, 5)

        self.main_start = wx.Button(self, wx.ID_ANY, u"启动", wx.DefaultPosition, wx.DefaultSize, 0)
        self.main_start.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.main_start, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.main_reset = wx.Button(self, wx.ID_ANY, u"重置", wx.DefaultPosition, wx.DefaultSize, 0)
        self.main_reset.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.main_reset, 0, wx.ALL, 5)

        self.m_staticText4121 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText4121.Wrap(-1)

        fgSizer3.Add(self.m_staticText4121, 0, wx.ALL, 5)

        self.m_staticText271 = wx.StaticText(self, wx.ID_ANY, u"简略战斗模块", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText271.Wrap(-1)

        self.m_staticText271.SetFont(
            wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "黑体"))

        fgSizer3.Add(self.m_staticText271, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_BOTTOM, 5)

        self.m_staticText411 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText411.Wrap(-1)

        fgSizer3.Add(self.m_staticText411, 0, wx.ALL, 5)

        self.m_staticText412 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(-1, 40), 0)
        self.m_staticText412.Wrap(-1)

        fgSizer3.Add(self.m_staticText412, 0, wx.ALL, 5)

        self.m_staticText4312 = wx.StaticText(self, wx.ID_ANY, u"NAME", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText4312.Wrap(-1)

        self.m_staticText4312.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.m_staticText4312, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.slim_battle_name = wx.TextCtrl(self, wx.ID_ANY, u"GT-6", wx.DefaultPosition, wx.DefaultSize, 0)
        fgSizer3.Add(self.slim_battle_name, 0, wx.ALL, 5)

        self.slim_battle_time = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                            wx.SP_ARROW_KEYS, 0, 100, 1)
        fgSizer3.Add(self.slim_battle_time, 0, wx.ALL | wx.EXPAND, 5)

        self.slim_start = wx.Button(self, wx.ID_ANY, u"启动", wx.DefaultPosition, wx.DefaultSize, 0)
        self.slim_start.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.slim_start, 0, wx.ALL, 5)

        self.slim_reset = wx.Button(self, wx.ID_ANY, u"重置", wx.DefaultPosition, wx.DefaultSize, 0)
        self.slim_reset.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.slim_reset, 0, wx.ALL, 5)

        fgSizer2.Add(fgSizer3, 1, wx.EXPAND, 5)

        self.out_put_ctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(200, 500),
                                        wx.TE_READONLY | wx.TE_MULTILINE)
        self.out_put_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

        fgSizer2.Add(self.out_put_ctrl, 0, wx.ALL, 5)

        bSizer2.Add(fgSizer2, 1, wx.EXPAND, 5)

        self.SetSizer(bSizer2)
        self.Layout()
        # self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        self.m_statusBar1 = self.CreateStatusBar(1, wx.STB_SIZEGRIP, wx.ID_ANY)

        # self.m_toolBar1 = self.CreateToolBar(wx.TB_HORIZONTAL, wx.ID_ANY)
        # self.m_tool1 = self.m_toolBar1.AddTool(wx.ID_ANY, u"tool",
        #                                        wx.Bitmap(u"GUI/Misc/setting2.png", wx.BITMAP_TYPE_ANY),
        #                                        wx.NullBitmap,
        #                                        wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None)
        # self.m_toolBar1.Realize()

        self.Centre(wx.BOTH)

        # Connect Events
        self.main_reset.Bind(wx.EVT_BUTTON, self.reset_main)
        self.slim_reset.Bind(wx.EVT_BUTTON, self.reset_slim)

    def __del__(self):
        pass

    # Virtual event handlers, overide them in your derived class

    def reset_main(self, event):
        self.task1_battle_name.SetValue("")
        self.task1_battle_time.SetValue(0)
        self.task2_battle_name.SetValue("")
        self.task2_battle_time.SetValue(0)
        self.task3_battle_name.SetValue("")
        self.task3_battle_time.SetValue(0)
        self.task4_battle_name.SetValue("")
        self.task4_battle_time.SetValue(0)
        return True

    def reset_slim(self, event):
        self.slim_battle_name.SetValue("")
        self.slim_battle_time.SetValue(0)
        return True
