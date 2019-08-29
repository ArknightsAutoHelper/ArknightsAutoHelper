@echo off
pyinstaller -F GUI_start.py
mv dist/GUI_start.exe ./