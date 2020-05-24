@echo off
chcp>nul 2>nul 65001
rem 切换至 ArknightsAutoHelper 所在位置
:path
cd>nul 2>nul /D %~dp0
call venv\Scripts\activate.bat

rem 主要循环节
:main
echo [92m[+] :)欢迎使用 ArknightsAutoHelper [0m
echo [92m[+] 输入 '1' 快速护肝[0m
rem echo [92m[+] 输入 '2' 计划任务[0m # 'set /p' 传入空格 Error待修复#
echo [92m[+] 输入 '2' 公招查询[0m
echo [92m[+] 输入 '3' 收获信赖[0m
echo [92m[+] 输入 '4' 任务领取[0m
echo [92m[+] 输入 '5' 结束服务[0m
:input
set /p a="[92m[+] 请选择需要的功能：[0m"
if /i '%a%'=='1' goto slim
rem if /i '%a%'=='2' goto hander
if /i '%a%'=='2' goto recruit
if /i '%a%'=='3' goto credit
if /i '%a%'=='4' goto task
if /i '%a%'=='5' goto end
echo [31m[x] 输入有误，请重新输入：[0m & goto input

rem 快速护肝
:slim
echo [93m[!] 正在唤起 ArknightsAutoHelper [1m
set /p slim="[94m[i] 输入预期战斗次数：[0m"
python akhelper.py quick %slim%

rem 快速护肝 - 确认是否重新运行
set /p aah1="[92m[+] 输入 '1' 返回首页 | 输入 '2' 助手下班 | 任意键再次运行：[0m"
if not '%aah1%'=='' set choice=%aah1:~0,1%
if '%aah1%'=='1' goto remain
if '%aah1%'=='2' goto end
goto :slim

rem rem 计划任务
rem :hander
rem echo [93m[!] 正在唤起 ArknightsAutoHelper [1m
rem set /p hander="[94m[i] 输入清单(关卡名 次数) 例如 "5-1 2 5-2 3" :[0m"
rem python akhelper.py auto %hander%
rem 
rem rem 计划任务 - 确认是否重新运行
rem set /p aah1="[92m[+] 输入 '1' 返回首页 | 输入 '2' 助手下班 | 任意键继续加班：[0m"
rem if not '%aah1%'=='' set choice=%aah1:~0,1%
rem if '%aah1%'=='1' goto remain
rem if '%aah1%'=='2' goto end

rem 公招查询
:recruit
echo [93m[!] 正在唤起 ArknightsAutoHelper [1m
python akhelper.py recruit
goto remain

rem 收获信赖
:credit
echo [93m[!] 正在唤起 ArknightsAutoHelper [1m
python ArknightsShell.py -r
goto remain

rem 任务领取
:task
echo [93m[!] 正在准备提供服务[1m
python akhelper.py collect
goto remain

:remain
rem 任务领取 - 确认是否重新运行
set /p task1="[92m[+] 输入 '1' 返回首页 | 任意键助手下班：[0m"
if not '%task1%'=='' set choice=%task1:~0,1%
if '%task1%'=='1' goto main
goto end

:end
echo [93m[!] 拜拜嘞您（3秒后下班）[1m
TIMEOUT>nul 2>nul /T 3
@exit
