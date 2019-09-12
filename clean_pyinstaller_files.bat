@echo off
del /f /s  build\*.*
rd /f /s /q build
rd dist
del "ArknightsShell.exe"
del "ArknightsShell.spec"