@echo off
set /p SCRIPTS=Path to original Data\Scripts.rxdata: 
if not exist build mkdir build
ruby toolchain\patch_essentials_language.rb "%SCRIPTS%" build\Scripts.rxdata zh_tw "Traditional Chinese"
pause
