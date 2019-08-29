@echo off
del /f /s  build/*.*
rd /f /s /q build
rd dist
del "GUI_start.exe"
del "GUI_start.spec"