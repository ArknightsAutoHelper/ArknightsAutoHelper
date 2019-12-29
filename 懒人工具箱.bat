@echo off
rem 切换至 ArknightsAutoHelper 所在位置
:path
cd>nul 2>nul /D %~dp0

rem 主要循环节
:main
echo [92m[+] :)欢迎使用 ArknightsAutoHelper [0m
echo [92m[+] 输入 '1' 快速启动(Slim模式)[0m
echo [92m[+] 输入 '2' 自动寻关(Hander模式)[0m
echo [92m[+] 输入 '3' 任务领取[0m
echo [92m[+] 输入 '4' 退出工具箱[0m
:input
set /p a="[92m[+] 请选择需要的功能：[0m"
if /i '%a%'=='1' goto slim
if /i '%a%'=='2' goto as
if /i '%a%'=='3' goto task
if /i '%a%'=='4' goto end
echo [31m[x] 输入有误，请重新输入：[0m & goto input

rem 急速护肝
:slim
echo [93m[!] 正在唤起 ArknightsAutoHelper [1m
set /p slim="[94m[i] 输入预期战斗次数：[0m"
python ArknightsShell.py -s -t slim:%slim%

rem 确认是否重新运行
set /p aah1="[92m[+] 输入 '1' 前往签到 | 输入 '2' 助手下班 | 任意键继续加班：[0m"
if not '%aah1%'=='' set choice=%aah1:~0,1%
if '%aah1%'=='1' goto task
if '%aah1%'=='2' goto end
goto :slim

rem 拉个清单
:as
echo [93m[!] 正在唤起 ArknightsAutoHelper [1m
set /p hander="[94m[i] 输入清单 例如 CE-5:1|LS-5:1 :[0m"
python ArknightsShell.py -b -t "%hander%"

rem 确认是否重新运行
set /p aah1="[92m[+] 输入 '1' 前往签到 | 输入 '2' 助手下班 | 任意键继续加班：[0m"
if not '%aah1%'=='' set choice=%aah1:~0,1%
if '%aah1%'=='1' goto task
if '%aah1%'=='2' goto end
goto as

rem 任务领取
:task
echo [93m[!] 正在准备提供服务[1m
python ArknightsShell.py -c

rem 确认是否重新运行
set /p task1="[92m[+] 输入 '1' 继续护肝 | 任意键助手下班：[0m"
if not '%task1%'=='' set choice=%ctask1:~0,1%
if '%task1%'=='1' goto main
goto end

:end
echo [93m[!] 拜拜嘞您（3秒后下班）[1m
TIMEOUT>nul 2>nul /T 3
@exit
