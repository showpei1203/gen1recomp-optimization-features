@echo off
set /p GAME=Pokemon Essentials game folder: 
if not exist work mkdir work
ruby toolchain\essentials_v21_dat_bridge.rb export "%GAME%\Data\messages_game.dat" "%GAME%\Data\messages_english_game.dat" work\v21_messages_manifest.tsv
pause
