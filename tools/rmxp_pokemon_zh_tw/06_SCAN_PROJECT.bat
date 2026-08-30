@echo off
set /p GAME=RMXP game folder path: 
if not exist build mkdir build
python toolchain\rmxp_zh_tw.py scan "%GAME%" --report build\project_text_scan.tsv
pause
