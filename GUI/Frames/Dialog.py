import wx


def MessageDialog_Yes_No(message=u"消息对话框测试", title=u"标题信息"):
    dlg = wx.MessageDialog(None, message, title, wx.YES_NO | wx.ICON_QUESTION)
    if dlg.ShowModal() == wx.ID_YES:
        dlg.Destroy()
        return True
    else:
        dlg.Destroy()
        return False


def MessageDialog_OK(message=u"消息对话框测试", title=u"标题信息"):
    dlg = wx.MessageDialog(None, message, title, wx.OK | wx.ICON_ERROR)
    if dlg.ShowModal() == wx.ID_OK:
        dlg.Destroy()
        return True


def MessageDialog_CANCEL(message=u"消息对话框测试", title=u"标题信息"):
    dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.ICON_INFORMATION)
    if dlg.ShowModal() == wx.ID_CANCEL:
        dlg.Destroy()
        return True
