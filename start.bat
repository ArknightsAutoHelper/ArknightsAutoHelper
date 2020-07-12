echo ArknightsAutoHelper is going to run in 60 seconds, if you don't need it, close this cmd.
@echo off
timeout 60
rem 修改ArknightsAutoHelper的路径和盘符
cd /D E:\Projects\ArknightsAutoHelper
rem 修改夜神模拟器的路径
set emuPath=F:\Nox\bin

rem 打开夜神模拟器
start "" "%emuPath%"nox.exe
timeout 120
rem 打开明日方舟
"%emuPath%"\adb.exe -s 127.0.0.1:62001 shell am start -n com.hypergryph.arknights/com.u8.sdk.U8UnityContext
timeout 120
rem 点击展示页
"%emuPath%"\adb.exe -s 127.0.0.1:62001 shell input tap 932 679
timeout 30
rem 点击账号管理
"%emuPath%"\adb.exe -s 127.0.0.1:62001 shell input tap 932 679
timeout 10
rem 点击账号登录
"%emuPath%"\adb.exe -s 127.0.0.1:62001 shell input tap 411 507
timeout 10
rem 点击密码
"%emuPath%"\adb.exe -s 127.0.0.1:62001 shell input tap 637 482
timeout 10
rem 输入密码
"%emuPath%"\adb.exe -s 127.0.0.1:62001 shell input text ******
timeout 10
rem 点击密码
"%emuPath%"\adb.exe -s 127.0.0.1:62001 shell input tap 637 482
timeout 10
rem 点击登录
"%emuPath%"\adb.exe -s 127.0.0.1:62001 shell input tap 640 575
timeout 60
python start.py
timeout 10
rem 关闭夜神模拟器
taskkill /f /im nox.exe
rem 关闭电脑
shutdown /s /t 60 /c "All the actions in Arknights finished, the computer will shutdown in 60 seconds."
