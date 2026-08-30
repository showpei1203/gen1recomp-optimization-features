@echo off
set /p GAME=Drag/type RMXP game folder path: 
python toolchain\rmxp_zh_tw.py detect "%GAME%"
pause
