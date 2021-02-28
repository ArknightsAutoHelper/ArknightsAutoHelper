@echo off
chcp>nul 2>nul 65001

rem 切换至 ArknightsAutoHelper 所在位置
:path
cd>nul 2>nul /D %~dp0
call venv\Scripts\activate.bat

rem 主任务
python run_plan.py


rem 结束进程
:end
echo [93m[!] 拜拜嘞您[1m
TIMEOUT>nul 2>nul /T 3
@exit

