@echo off
rem ÇÐ»»ÖÁ ArknightsAutoHelper ËùÔÚÎ»ÖÃ
:path
cd>nul 2>nul /D %~dp0

rem Ö÷ÒªÑ­»·½Ú
:main
echo [92m[+] :)»¶Ó­Ê¹ÓÃ ArknightsAutoHelper [0m
echo [92m[+] ÊäÈë '1' ¿ìËÙÆô¶¯(SlimÄ£Ê½)[0m
echo [92m[+] ÊäÈë '2' ×Ô¶¯Ñ°¹Ø(HanderÄ£Ê½)[0m
echo [92m[+] ÊäÈë '3' ÈÎÎñÁìÈ¡[0m
echo [92m[+] ÊäÈë '4' ÍË³ö¹¤¾ßÏä[0m
:input
set /p a="[92m[+] ÇëÑ¡ÔñÐèÒªµÄ¹¦ÄÜ£º[0m"
if /i '%a%'=='1' goto slim
if /i '%a%'=='2' goto as
if /i '%a%'=='3' goto task
if /i '%a%'=='4' goto end
echo [31m[x] ÊäÈëÓÐÎó£¬ÇëÖØÐÂÊäÈë£º[0m & goto input

rem ¼±ËÙ»¤¸Î
:slim
echo [93m[!] ÕýÔÚ»½Æð ArknightsAutoHelper [1m
set /p slim="[94m[i] ÊäÈëÔ¤ÆÚÕ½¶·´ÎÊý£º[0m"
python ArknightsShell.py -s -t slim:%slim%

rem È·ÈÏÊÇ·ñÖØÐÂÔËÐÐ
set /p aah1="[92m[+] ÊäÈë '1' Ç°ÍùÇ©µ½ | ÊäÈë '2' ÖúÊÖÏÂ°à | ÈÎÒâ¼ü¼ÌÐø¼Ó°à£º[0m"
if not '%aah1%'=='' set choice=%aah1:~0,1%
if '%aah1%'=='1' goto task
if '%aah1%'=='2' goto end
goto :slim

rem À­¸öÇåµ¥
:as
echo [93m[!] ÕýÔÚ»½Æð ArknightsAutoHelper [1m
set /p hander="[94m[i] ÊäÈëÇåµ¥ ÀýÈç CE-5:1|LS-5:1 :[0m"
python ArknightsShell.py -b -t "%hander%"

rem È·ÈÏÊÇ·ñÖØÐÂÔËÐÐ
set /p aah1="[92m[+] ÊäÈë '1' Ç°ÍùÇ©µ½ | ÊäÈë '2' ÖúÊÖÏÂ°à | ÈÎÒâ¼ü¼ÌÐø¼Ó°à£º[0m"
if not '%aah1%'=='' set choice=%aah1:~0,1%
if '%aah1%'=='1' goto task
if '%aah1%'=='2' goto end
goto as

rem ÈÎÎñÁìÈ¡
:task
echo [93m[!] ÕýÔÚ×¼±¸Ìá¹©·þÎñ[1m
python ArknightsShell.py -c

rem È·ÈÏÊÇ·ñÖØÐÂÔËÐÐ
set /p task1="[92m[+] ÊäÈë '1' ¼ÌÐø»¤¸Î | ÈÎÒâ¼üÖúÊÖÏÂ°à£º[0m"
if not '%task1%'=='' set choice=%ctask1:~0,1%
if '%task1%'=='1' goto main
goto end

:end
echo [93m[!] °Ý°ÝàÏÄú£¨3ÃëºóÏÂ°à£©[1m
TIMEOUT>nul 2>nul /T 3
@exit
