'''suppress creation of gen_py directory'''

def GetGeneratedInfos(*args, **kwargs):
    return []

def _none_impl(*args, **kwargs):
    return None

def _notimpl_impl(*args, **kwargs):
    raise NotImplementedError

globals().update((x, _none_impl) for x in ['GetClassForCLSID', 'GetClassForProgID', 'GetModuleForCLSID', 'GetModuleForTypelib', 'ForgetAboutTypelibInterface', 'AddModuleToCache'])
globals().update((x, _notimpl_impl) for x in ['MakeModuleForTypelib', 'MakeModuleForTypelibInterface', 'EnsureModuleForTypelibInterface', 'EnsureModule', 'EnsureDispatch'])

import sys
this_module = sys.modules[__name__]
sys.modules['win32com.client.gencache'] = this_module

del this_module
