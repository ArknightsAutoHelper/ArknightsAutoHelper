@echo off
setlocal EnableDelayedExpansion
set PYTHON_EXECUTABLE=python3
where /q py
if errorlevel 0 set PYTHON_EXECUTABLE=py
cd /d "%~dp0"
!PYTHON_EXECUTABLE! -m venv venv
call venv\Scripts\activate.bat
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt
endlocal
