@echo off
set /p BASELINE=Baseline translated messages DAT path: 
if not exist build mkdir build
ruby toolchain\essentials_v21_dat_bridge.rb qa work\v21_messages_manifest.tsv build\v21_qa.tsv zh_tw
if errorlevel 1 goto :fail
ruby toolchain\essentials_v21_dat_bridge.rb build "%BASELINE%" work\v21_messages_manifest.tsv build\messages_zh_tw_game.dat zh_tw
echo Build complete.
pause
exit /b 0
:fail
echo QA failed. Check build\v21_qa.tsv
pause
exit /b 1
