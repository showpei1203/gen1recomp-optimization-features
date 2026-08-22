@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title Collect SBFX ScreenFx Bypass A/B Evidence
set "PKG=io.github.averageconsumer.gen1recomp.androidtest"
set "ROOT=/storage/emulated/0/Android/data/io.github.averageconsumer.gen1recomp.androidtest/files/save/pokemon-love2d"
set "SBFX=%ROOT%/mods/STADIUM_BATTLE_FX"
set "PMD=%ROOT%/mods/pmd_idle_battle_sprites"
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%I"
set "OUT=%USERPROFILE%\Desktop\SBFX_SCREENFX_BYPASS_EVIDENCE_!TS!"
mkdir "!OUT!" >nul 2>&1
where adb >nul 2>&1 || goto NOADB
adb get-state >nul 2>&1 || goto NODEVICE

echo Collecting hashes and clean runtime log...
adb exec-out run-as %PKG% sha256sum "%SBFX%/main.lua" > "!OUT!\SBFX_MAIN_SHA256.txt" 2>nul
adb exec-out run-as %PKG% cat "%SBFX%/manifest.json" > "!OUT!\SBFX_manifest.json" 2>nul
adb exec-out run-as %PKG% sha256sum "%PMD%/main.lua" > "!OUT!\PMD_MAIN_SHA256.txt" 2>nul
adb logcat -d -v threadtime > "!OUT!\logcat.txt" 2>nul
adb exec-out run-as %PKG% sh -c "grep -n 'GEN1RECOMP_SCREENFX_PRESENT_BYPASS_TEST' '%SBFX%/main.lua' || true" > "!OUT!\BYPASS_MARKER.txt" 2>nul
if exist "%~dp0APPLY_RESULT.txt" copy /y "%~dp0APPLY_RESULT.txt" "!OUT!\APPLY_RESULT.txt" >nul

>"!OUT!\USER_RESULT.txt" echo Please fill these four lines before uploading:
>>"!OUT!\USER_RESULT.txt" echo SQUARE_MASK=GONE_or_STILL_PRESENT
>>"!OUT!\USER_RESULT.txt" echo QUICK_ATTACK_ANIM=YES_or_NO
>>"!OUT!\USER_RESULT.txt" echo EMBER_ANIM=YES_or_NO
>>"!OUT!\USER_RESULT.txt" echo FURY_SWIPES_ANIM=YES_or_NO

powershell -NoProfile -Command "Compress-Archive -LiteralPath '!OUT!\*' -DestinationPath '!OUT!.zip' -Force" >nul 2>&1

echo.
echo [PASS] Evidence written to:
echo   !OUT!.zip
echo.
echo Fill USER_RESULT.txt if convenient, or just tell ChatGPT whether the square mask disappeared and whether move animations remained.
pause
exit /b 0
:NOADB
echo [FAIL] adb not found.&pause&exit /b 2
:NODEVICE
echo [FAIL] Android device unavailable.&pause&exit /b 3
