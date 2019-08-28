echo ArknightsAutoHelper is going to run in 60 seconds, if you don't need it, close this cmd.
timeout 60
@echo off
SET noxPath=F:\Nox\bin\nox.exe
SET adbPath=F:\Nox\bin\adb.exe
rem 打开夜神模拟器
start %noxPath%
timeout 60
rem 打开明日方舟
%abdPath% -s 127.0.0.1:62001 shell am start -n com.hypergryph.arknights/com.u8.sdk.U8UnityContext
timeout 20
rem 点击展示页
%abdPath% -s 127.0.0.1:62001 shell input tap 932 679
timeout 5
rem 点击账号管理
%abdPath% -s 127.0.0.1:62001 shell input tap 932 679
timeout 3
rem 点击账号登录
%abdPath% -s 127.0.0.1:62001 shell input tap 411 507
timeout 3
rem 点击密码
%abdPath% -s 127.0.0.1:62001 shell input tap 637 482
timeout 3
rem 输入密码
%abdPath% -s 127.0.0.1:62001 shell input text ******
timeout 3
rem 点击密码
%abdPath% -s 127.0.0.1:62001 shell input tap 637 482
timeout 3
rem 点击登录
%abdPath% -s 127.0.0.1:62001 shell input tap 640 575
timeout 10
python E:\Projects\ArknightsAutoHelper\start.py
rem 关闭夜神模拟器
taskkill /f /im nox.exe
rem 关闭电脑
shutdown /s /t 60 /c "All the actions in Arknights finished, the computer will shutdown in 60 seconds."