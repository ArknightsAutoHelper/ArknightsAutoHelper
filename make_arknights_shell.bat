@echo off
pyinstaller -F ArknightsShell.py
move dist\ArknightsShell.exe .
rd dist