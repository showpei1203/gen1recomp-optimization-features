@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title Gen1recomp SBFX ScreenFx.present BYPASS A/B TEST

set "PKG=io.github.averageconsumer.gen1recomp.androidtest"
set "ROOT=/storage/emulated/0/Android/data/io.github.averageconsumer.gen1recomp.androidtest/files/save/pokemon-love2d"
set "SBFX=%ROOT%/mods/STADIUM_BATTLE_FX"
set "MAIN=%SBFX%/main.lua"
set "MANIFEST=%SBFX%/manifest.json"
set "PMD=%ROOT%/mods/pmd_idle_battle_sprites"
set "LOG=%~dp0APPLY_RESULT.txt"
set "TMP_ORIG=%TEMP%\sbfx_screenfx_orig.lua"
set "TMP_PATCH=%TEMP%\sbfx_screenfx_patch.lua"

>"%LOG%" echo Gen1recomp StadiumBattleFX ScreenFx.present Bypass Probe
>>"%LOG%" echo ======================================================

echo.
echo ======================================================
echo  StadiumBattleFX ScreenFx.present BYPASS A/B TEST
echo  ONLY bypasses the post-compose ScreenFx.present call.
echo  It does NOT disable Stadium move animations.
echo ======================================================
echo.

where adb >nul 2>&1 || goto NOADB
adb get-state >nul 2>&1 || goto NODEVICE

echo [1/8] Stop game...
adb shell am force-stop %PKG% >nul 2>&1

echo [2/8] Verify StadiumBattleFX direct mod path...
adb exec-out run-as %PKG% test -f "%MANIFEST%" || goto NOSBFX
adb exec-out run-as %PKG% test -f "%MAIN%" || goto NOSBFX

echo [3/8] Read exact installed StadiumBattleFX main.lua...
adb exec-out run-as %PKG% cat "%MAIN%" > "%TMP_ORIG%" || goto READFAIL
for /f "tokens=1" %%H in ('certutil -hashfile "%TMP_ORIG%" SHA256 ^| findstr /R /V "hash CertUtil"') do set "ORIGSHA=%%H"
echo [INFO] Original SBFX main SHA256=!ORIGSHA!
>>"%LOG%" echo ORIGINAL_SHA256=!ORIGSHA!

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%I"
set "BACK=%USERPROFILE%\Desktop\GEN1RECOMP_SBFX_SCREENFX_PRE_BYPASS_!TS!"
mkdir "!BACK!" >nul 2>&1
copy /y "%TMP_ORIG%" "!BACK!\main.lua" >nul || goto BACKUPFAIL
adb exec-out run-as %PKG% cat "%MANIFEST%" > "!BACK!\manifest.json" 2>nul
>"!BACK!\README_RESTORE.txt" echo This is the exact pre-bypass StadiumBattleFX snapshot. Use RESTORE_SBFX_SCREENFX_PRESENT_BYPASS.bat from the probe package.
>"%~dp0LAST_SBFX_SCREENFX_BACKUP.txt" echo !BACK!

echo [4/8] Build one-line bypass patch locally...
set "PS1=%TEMP%\sbfx_screenfx_patch_%RANDOM%.ps1"
>"!PS1!" echo $ErrorActionPreference = 'Stop'
>>"!PS1!" echo $p = $env:TMP_ORIG
>>"!PS1!" echo $o = $env:TMP_PATCH
>>"!PS1!" echo $s = [IO.File]::ReadAllText($p)
>>"!PS1!" echo $pattern = 'if\s+stadiumOwns\("effects"\)\s+then\s+StadiumScreenFx\.present\(game,\s*viewport\)\s+end'
>>"!PS1!" echo $m = [regex]::Matches($s, $pattern)
>>"!PS1!" echo if ($m.Count -ne 1) { throw "Expected exactly 1 StadiumScreenFx.present render.hud call, found $($m.Count)" }
>>"!PS1!" echo $replacement = 'if false and stadiumOwns("effects") then StadiumScreenFx.present(game, viewport) end -- GEN1RECOMP_SCREENFX_PRESENT_BYPASS_TEST'
>>"!PS1!" echo $n = [regex]::Replace($s, $pattern, $replacement, 1)
>>"!PS1!" echo [IO.File]::WriteAllText($o, $n, (New-Object Text.UTF8Encoding($false)))
powershell -NoProfile -ExecutionPolicy Bypass -File "!PS1!" || goto PATCHFAIL
del /q "!PS1!" >nul 2>&1
findstr /C:"GEN1RECOMP_SCREENFX_PRESENT_BYPASS_TEST" "%TMP_PATCH%" >nul || goto PATCHFAIL

for /f "tokens=1" %%H in ('certutil -hashfile "%TMP_PATCH%" SHA256 ^| findstr /R /V "hash CertUtil"') do set "PATCHSHA=%%H"
echo [INFO] Patched SBFX main SHA256=!PATCHSHA!
>>"%LOG%" echo PATCHED_SHA256=!PATCHSHA!
>>"%LOG%" echo BACKUP=!BACK!

echo [5/8] Write patched main.lua to Android...
adb exec-in run-as %PKG% sh -c "cat > '%MAIN%'" < "%TMP_PATCH%" || goto WRITEFAIL

echo [6/8] Verify remote patched hash + marker...
set "REMOTESHA="
for /f "tokens=1" %%H in ('adb exec-out run-as %PKG% sha256sum "%MAIN%" 2^>nul') do set "REMOTESHA=%%H"
if /I not "!REMOTESHA!"=="!PATCHSHA!" goto VERIFYFAIL
adb exec-out run-as %PKG% grep -q "GEN1RECOMP_SCREENFX_PRESENT_BYPASS_TEST" "%MAIN%" || goto VERIFYFAIL

set "PMDSHA="
for /f "tokens=1" %%H in ('adb exec-out run-as %PKG% sha256sum "%PMD%/main.lua" 2^>nul') do set "PMDSHA=%%H"
>>"%LOG%" echo PMD_MAIN_SHA256=!PMDSHA!

echo [7/8] Clear logcat for clean A/B run...
adb logcat -c >nul 2>&1

echo [8/8] APPLY PASS.
>>"%LOG%" echo RESULT=PASS

echo.
echo ======================================================
echo  APPLY PASS
echo ======================================================
echo  Now launch Gen1Recomp.
echo  Keep STADIUM FX = ON.
echo  Enter the same B-fixture battle.
echo.
echo  ONLY judge these two items first:
echo    1. Is the square battle mask gone?
echo    2. Do Quick Attack / Ember / Fury Swipes animations still play?
echo.
echo  Surf fidelity is NOT the pass/fail criterion for this probe.
echo  Do not change PMD / DS / THOR settings during this A/B test.
echo.
echo  Exact pre-patch backup:
echo    !BACK!
echo.
echo  If needed, run RESTORE_SBFX_SCREENFX_PRESENT_BYPASS.bat.
echo ======================================================
pause
exit /b 0

:NOADB
echo [FAIL] adb not found in PATH.&>>"%LOG%" echo RESULT=FAIL NO_ADB&pause&exit /b 2
:NODEVICE
echo [FAIL] Android device unavailable.&>>"%LOG%" echo RESULT=FAIL NO_DEVICE&pause&exit /b 3
:NOSBFX
echo [FAIL] StadiumBattleFX main.lua/manifest.json not found at direct mod path.&>>"%LOG%" echo RESULT=FAIL SBFX_NOT_FOUND&pause&exit /b 10
:READFAIL
echo [FAIL] Could not read installed StadiumBattleFX main.lua.&>>"%LOG%" echo RESULT=FAIL READ&pause&exit /b 11
:BACKUPFAIL
echo [FAIL] Could not create exact Desktop backup. Nothing changed.&>>"%LOG%" echo RESULT=FAIL BACKUP&pause&exit /b 12
:PATCHFAIL
echo [FAIL] Exact ScreenFx.present call was not found exactly once. Nothing changed.&>>"%LOG%" echo RESULT=FAIL PATCH_PATTERN&pause&exit /b 13
:WRITEFAIL
echo [FAIL] Android write failed. Run restore if necessary.&>>"%LOG%" echo RESULT=FAIL WRITE&pause&exit /b 14
:VERIFYFAIL
echo [FAIL] Post-write hash/marker verification failed. Run restore now.&>>"%LOG%" echo RESULT=FAIL VERIFY&pause&exit /b 15
