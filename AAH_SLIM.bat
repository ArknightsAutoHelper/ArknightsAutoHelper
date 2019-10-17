@echo off
set 1>nul 2>nul HTTP_PROXY=http://127.0.0.1:1080
set 1>nul 2>nul HTTPS_PROXY=http://127.0.0.1:1080
chcp 1>nul 2>nul 65001

rem 切换至护肝助手所在位置
:path
adb 1>nul 2>nul connect 127.0.0.1:7555
cd 1>nul 2>nul /D %~dp0

rem 护肝助手主任务
:aah_slim
python ArknightsShell.py -s -t slim:999
goto file

rem 记录掉落信息
:file
findstr 1>nul 2>nul /c "stars" log\*ArknightsAutoHelper.log
If ErrorLevel 1 ( goto end ) Else ( goto do )
:do
findstr 1>nul 2>nul "stars" log\ArknightsAutoHelper.log >> ..\"掉落查看.txt"
findstr 1>nul 2>nul "stars ID" log\ArknightsAutoHelper.log >> ..\"企鹅物流.txt"
del 1>nul 2>nul /s /Q log
start ..\"掉落查看.txt"
goto end

rem 结束进程
:end
exit
rem pause