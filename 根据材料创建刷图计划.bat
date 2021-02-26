@echo off
chcp>nul 2>nul 65001

rem 切换至 ArknightsAutoHelper 所在位置
:path
cd>nul 2>nul /D %~dp0
call venv\Scripts\activate.bat


python create_plan_by_item.py
