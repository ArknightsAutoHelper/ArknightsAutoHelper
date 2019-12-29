@echo off
chcp>nul 2>nul 65001

rem 切换至 ArknightsAutoHelper 所在位置
:path
cd>nul 2>nul /D %~dp0

rem 主任务
:aah_slim
set /p slim="[94m[i] 输入预期战斗次数：[0m "
python ArknightsShell.py -s -t slim:%slim%

rem 确认是否重新运行
set /p choice="[94m[i] 输入 'y' 重新运行 | 任意键退出：[0m"
if not '%choice%'=='' set choice=%choice:~0,1%
if '%choice%'=='y' goto aah_slim
goto end

rem 结束进程
:end
echo [93m[!] 拜拜嘞您[1m
TIMEOUT>nul 2>nul /T 3
@exit

