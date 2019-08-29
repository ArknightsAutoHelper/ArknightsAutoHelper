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
## Class Index
###########################################################################

class Index(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"Arknights Auto Helper GUI V0.1 beta By shaobaobaoer",
                          pos=wx.DefaultPosition, size=wx.Size(835, 657),
                          style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

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

        self.m_staticText4151 = wx.StaticText(self, wx.ID_ANY, u"辅助操作模块", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText4151.Wrap(-1)

        self.m_staticText4151.SetFont(
            wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "黑体"))

        fgSizer3.Add(self.m_staticText4151, 0, wx.ALL, 5)

        self.m_staticText4131 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText4131.Wrap(-1)

        fgSizer3.Add(self.m_staticText4131, 0, wx.ALL, 5)

        self.m_staticText41311 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(-1, 30), 0)
        self.m_staticText41311.Wrap(-1)

        fgSizer3.Add(self.m_staticText41311, 0, wx.ALL, 5)

        self.init_ark = wx.Button(self, wx.ID_ANY, u"初始化辅助", wx.DefaultPosition, wx.DefaultSize, 0)
        self.init_ark.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.init_ark, 0, wx.ALL, 5)

        self.login = wx.Button(self, wx.ID_ANY, u"登陆", wx.DefaultPosition, wx.DefaultSize, 0)
        self.login.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.login, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.reboot = wx.Button(self, wx.ID_ANY, u"重启", wx.DefaultPosition, wx.DefaultSize, 0)
        self.reboot.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.reboot, 0, wx.ALL, 5)

        self.m_staticText415 = wx.StaticText(self, wx.ID_ANY, u"设置当前理智", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText415.Wrap(-1)

        self.m_staticText415.SetFont(
            wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "黑体"))

        fgSizer3.Add(self.m_staticText415, 0, wx.ALL, 5)

        self.m_staticText414 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText414.Wrap(-1)

        fgSizer3.Add(self.m_staticText414, 0, wx.ALL, 5)

        self.m_staticText4141 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText4141.Wrap(-1)

        fgSizer3.Add(self.m_staticText4141, 0, wx.ALL, 5)

        self.set_init_strength = wx.Button(self, wx.ID_ANY, u"设置", wx.DefaultPosition, wx.DefaultSize, 0)
        self.set_init_strength.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.set_init_strength, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.m_staticText57 = wx.StaticText(self, wx.ID_ANY, u"当前理智", wx.DefaultPosition, wx.Size(-1, -1), 0)
        self.m_staticText57.Wrap(-1)

        self.m_staticText57.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.m_staticText57, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.current_lizhi = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(50, -1), 0)
        self.current_lizhi.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

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

        self.task1_battle_name = wx.TextCtrl(self, wx.ID_ANY, u"LS-5", wx.DefaultPosition, wx.DefaultSize, 0)
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
                                             wx.SP_ARROW_KEYS, 0, 100, 0)
        fgSizer3.Add(self.task2_battle_time, 0, wx.ALL | wx.EXPAND, 5)

        self.m_staticText4311 = wx.StaticText(self, wx.ID_ANY, u"TASK3", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText4311.Wrap(-1)

        self.m_staticText4311.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.m_staticText4311, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.task3_battle_name = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        fgSizer3.Add(self.task3_battle_name, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.task3_battle_time = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                             wx.SP_ARROW_KEYS, 0, 100, 0)
        fgSizer3.Add(self.task3_battle_time, 0, wx.ALL | wx.EXPAND, 5)

        self.m_staticText43111 = wx.StaticText(self, wx.ID_ANY, u"TASK4", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText43111.Wrap(-1)

        self.m_staticText43111.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.m_staticText43111, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.task4_battle_name = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        fgSizer3.Add(self.task4_battle_name, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.task4_battle_time = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                             wx.SP_ARROW_KEYS, 0, 100, 0)
        fgSizer3.Add(self.task4_battle_time, 0, wx.ALL | wx.EXPAND, 5)

        self.main_start = wx.Button(self, wx.ID_ANY, u"启动", wx.DefaultPosition, wx.DefaultSize, 0)
        self.main_start.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.main_start, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.main_reset = wx.Button(self, wx.ID_ANY, u"重置", wx.DefaultPosition, wx.DefaultSize, 0)
        self.main_reset.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.main_reset, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.main_kill = wx.Button(self, wx.ID_ANY, u"停止线程", wx.DefaultPosition, wx.DefaultSize, 0)
        self.main_kill.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.main_kill, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

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

        self.slim_battle_id_to_c_id = {
            "36理智关卡": "PR-B-2",
            "30理智关卡": "LS-5",
            "25理智关卡": "CA-4",
            "21理智关卡": "4-10",
            "20理智关卡": "CA-3",
            "18理智关卡": "4-9",
            "15理智关卡": "CA-2",
            "12理智关卡": "2-9",
            "10理智关卡": "CA-1",
        }
        m_choice1Choices = [x for x in self.slim_battle_id_to_c_id.keys()]
        self.slim_battle_name = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice1Choices,
                                          wx.CB_SORT)
        self.slim_battle_name.SetSelection(self.slim_battle_id_to_c_id.__len__())
        # self.m_choice1.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))
        # self.m_choice1.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        fgSizer3.Add(self.slim_battle_name, 0, wx.ALL, 5)

        self.slim_battle_time = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                            wx.SP_ARROW_KEYS, 0, 100, 99)
        fgSizer3.Add(self.slim_battle_time, 0, wx.ALL | wx.EXPAND, 5)

        self.slim_start = wx.Button(self, wx.ID_ANY, u"启动", wx.DefaultPosition, wx.DefaultSize, 0)
        self.slim_start.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.slim_start, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.slim_reset = wx.Button(self, wx.ID_ANY, u"重置", wx.DefaultPosition, wx.DefaultSize, 0)
        self.slim_reset.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.slim_reset, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.slim_kill = wx.Button(self, wx.ID_ANY, u"停止线程", wx.DefaultPosition, wx.DefaultSize, 0)
        self.slim_kill.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        fgSizer3.Add(self.slim_kill, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        fgSizer2.Add(fgSizer3, 1, wx.EXPAND, 5)

        self.out_put_ctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(200, 500),
                                        wx.TE_MULTILINE | wx.TE_READONLY)
        self.out_put_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

        fgSizer2.Add(self.out_put_ctrl, 0, wx.ALL, 5)

        bSizer2.Add(fgSizer2, 1, wx.EXPAND, 5)

        self.SetSizer(bSizer2)
        self.Layout()
        self.m_statusBar1 = self.CreateStatusBar(1, wx.STB_SIZEGRIP, wx.ID_ANY)
        self.menu_bar = wx.MenuBar(0)
        self.menu_bar.SetFont(
            wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "等线"))

        self.m_menu3 = wx.Menu()
        self.change_settings = wx.MenuItem(self.m_menu3, wx.ID_ANY, u"查看/修改设置", wx.EmptyString, wx.ITEM_NORMAL)
        self.m_menu3.Append(self.change_settings)

        self.about_me = wx.MenuItem(self.m_menu3, wx.ID_ANY, u"关于开发者", wx.EmptyString, wx.ITEM_NORMAL)
        self.m_menu3.Append(self.about_me)

        self.menu_bar.Append(self.m_menu3, u"设置")

        self.SetMenuBar(self.menu_bar)

        self.Centre(wx.BOTH)

    def __del__(self):
        pass
