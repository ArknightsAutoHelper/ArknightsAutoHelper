@echo off
chcp>nul 2>nul 65001

rem 切换至护肝助手所在位置
:path
cd>nul 2>nul /D %~dp0

rem 护肝助手主任务
:aah_slim
python ArknightsShell.py -u
goto end

rem 结束进程
:end
exit