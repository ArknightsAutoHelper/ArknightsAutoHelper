echo ArknightsAutoHelper is going to run in 60 seconds, if you don't need it, close this cmd.

timeout 5
rem 修改ArknightsAutoHelper的路径和盘符
cd /D D:\Python_Project\ArknightsHelper\ArknightsAutoHelper-master
rem 修改夜神模拟器的路径
set emuPath=D:\Program Files\MuMu\emulator\nemu\EmulatorShell

rem 打开夜神模拟器
start "" "%emuPath%"\NemuPlayer.exe
timeout 40
rem 打开明日方舟
"%emuPath%"\adb.exe kill-server
"%emuPath%"\adb.exe start-server
"%emuPath%"\adb.exe connect 127.0.0.1:7555
timeout 10
"%emuPath%"\adb.exe connect 127.0.0.1:7555
"%emuPath%"\adb.exe -s 127.0.0.1:7555 shell am start -n com.hypergryph.arknights/com.u8.sdk.U8UnityContext
timeout 30
rem 点击展示页
"%emuPath%"\adb.exe -s 127.0.0.1:7555 shell input tap 932 679
timeout 30
rem 点击账号管理
"%emuPath%"\adb.exe -s 127.0.0.1:7555 shell input tap 932 679
timeout 10
rem 点击账号登录
"%emuPath%"\adb.exe -s 127.0.0.1:7555 shell input tap 411 507
timeout 10
rem 点击密码
"%emuPath%"\adb.exe -s 127.0.0.1:7555 shell input tap 637 482
timeout 10
rem 输入密码
"%emuPath%"\adb.exe -s 127.0.0.1:7555 shell input text Kong.20040413
timeout 10
rem 点击密码
"%emuPath%"\adb.exe -s 127.0.0.1:7555 shell input tap 637 482
timeout 10
rem 点击登录
"%emuPath%"\adb.exe -s 127.0.0.1:7555 shell input tap 640 575
"%emuPath%"\adb.exe disconnect 127.0.0.1:7555
timeout 30
arkmain.py
timeout 10
rem 关闭夜神模拟器
gsudo taskkill /f /im NemuPlayer.exe
gsudo taskkill /f /im NemuHeadless.exe
rem 关闭电脑
rem shutdown /s /t 60 /c "All the actions in Arknights finished, the computer will shutdown in 60 seconds."
