@echo off
chcp 65001>nul 2>nul

echo [93m[!] 本批处理会清除历史log ！！！[1m
echo [93m[!] 本批处理会清除历史log ！！！[1m
echo [93m[!] 本批处理会清除历史log ！！！[1m
echo [93m[!] 运行过程中出现 BUG ，请先备份好对应的 log文件以便排除问题！！！[1m
echo [93m[!] 运行过程中出现 BUG ，请先备份好对应的 log文件以便排除问题！！！[1m
echo [93m[!] 运行过程中出现 BUG ，请先备份好对应的 log文件以便排除问题！！！[1m
set /p choice="[94m[i] 输入 'y' 继续 | 任意键退出：[0m"
if not '%choice%'=='' set choice=%choice:~0,1%
if '%choice%'=='y' goto history
goto end

:history
@findstr "stars" log\ArknightsAutoHelper.log>>物品掉落.txt
@del log\*.log*
echo [94m[i] 已将掉落信息添加至 物品掉落.txt 文件[0m

:end
echo [93m[!] 拜拜嘞您[1m
TIMEOUT>nul 2>nul /T 3
@exit
