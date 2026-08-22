@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title Restore StadiumBattleFX before ScreenFx bypass
set "PKG=io.github.averageconsumer.gen1recomp.androidtest"
set "ROOT=/storage/emulated/0/Android/data/io.github.averageconsumer.gen1recomp.androidtest/files/save/pokemon-love2d"
set "MAIN=%ROOT%/mods/STADIUM_BATTLE_FX/main.lua"

if not exist "%~dp0LAST_SBFX_SCREENFX_BACKUP.txt" goto NOBACK
set /p BACK=<"%~dp0LAST_SBFX_SCREENFX_BACKUP.txt"
if not exist "!BACK!\main.lua" goto NOBACK
where adb >nul 2>&1 || goto NOADB
adb get-state >nul 2>&1 || goto NODEVICE

echo Stop game...
adb shell am force-stop %PKG% >nul 2>&1

echo Restore exact pre-bypass StadiumBattleFX main.lua...
adb exec-in run-as %PKG% sh -c "cat > '%MAIN%'" < "!BACK!\main.lua" || goto FAIL
set "LOCAL="&set "REMOTE="
for /f "tokens=1" %%H in ('certutil -hashfile "!BACK!\main.lua" SHA256 ^| findstr /R /V "hash CertUtil"') do set "LOCAL=%%H"
for /f "tokens=1" %%H in ('adb exec-out run-as %PKG% sha256sum "%MAIN%" 2^>nul') do set "REMOTE=%%H"
if /I not "!LOCAL!"=="!REMOTE!" goto FAIL

echo.
echo [PASS] StadiumBattleFX exact pre-bypass main.lua restored.
echo SHA256=!REMOTE!
adb logcat -c >nul 2>&1
pause
exit /b 0
:NOBACK
echo [FAIL] Backup path not found. Nothing changed.&pause&exit /b 10
:NOADB
echo [FAIL] adb not found.&pause&exit /b 2
:NODEVICE
echo [FAIL] Android device unavailable.&pause&exit /b 3
:FAIL
echo [FAIL] Restore/write verification failed.&pause&exit /b 11
