@echo off
set /p SRC=Path to intl.txt or Text_* extracted folder: 
if not exist work mkdir work
python toolchain\rmxp_zh_tw.py export "%SRC%" --out work\translation_manifest.tsv
pause
