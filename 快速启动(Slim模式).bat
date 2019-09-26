@echo off

rem ÇÐ»»ÖÁ ArknightsAutoHelper ËùÔÚÎ»ÖÃ
:path
cd>nul 2>nul /D %~dp0

rem Ö÷ÈÎÎñ
:aah_slim
set /p slim="[94m[i] ÊäÈëÔ¤ÆÚÕ½¶·´ÎÊý[0m"
python ArknightsShell.py -s -t slim:%slim%

rem È·ÈÏÊÇ·ñÖØÐÂÔËÐÐ
set /p choice="[94m[i] ÊäÈë 'y' ÖØÐÂÔËÐÐ | ÈÎÒâ¼üÍË³ö£º[0m"
if not '%choice%'=='' set choice=%choice:~0,1%
if '%choice%'=='y' goto aah_slim
goto end

rem ½áÊø½ø³Ì
:end
echo [93m[!] °Ý°ÝàÏÄú[1m
TIMEOUT>nul 2>nul /T 3
@exit