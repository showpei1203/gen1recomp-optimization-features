@echo off
set /p SRC=Same extracted intl.txt or Text_* folder used in step 2: 
if not exist build mkdir build
python toolchain\rmxp_zh_tw.py build "%SRC%" work\translation_manifest.tsv --out build\Text_zh_tw
pause
