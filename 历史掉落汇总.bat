@echo off

echo [93m[!] ±¾Åú´¦Àí»áÇå³ýÀúÊ·log £¡£¡£¡[1m
set /p choice="[94m[i] ÊäÈë 'y' È·ÈÏ | ÈÎÒâ¼üÍË³ö£º[0m"
if not '%choice%'=='' set choice=%choice:~0,1%
if '%choice%'=='y' goto history
goto end

:history
@echo --------------------------------->>ÎïÆ·µôÂä.txt
@findstr "µôÂäÊ¶±ð½á¹û" log\ArknightsAutoHelper.log>>ÎïÆ·µôÂä.txt
@del log\*.log*
echo [94m[i] ÒÑ½«µôÂäÐÅÏ¢Ìí¼ÓÖÁ ÎïÆ·µôÂä.txt ÎÄ¼þ[0m

:end
echo [93m[!] °Ý°ÝàÏÄú[1m
TIMEOUT>nul 2>nul /T 3
@exit