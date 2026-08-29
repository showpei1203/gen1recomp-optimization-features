@echo off
setlocal
title SoulGoldRecomp S0-C2 - START Gate Progression
cls
echo ===============================================================
echo SoulGoldRecomp S0-C2 - START Gate Progression
echo ===============================================================
echo.
echo Toolfix9: PowerShell HOME automatic-variable collision fixed.
echo This reuses the sealed S0-B runner and S0-C1 BIOS/ROM.
echo It sends a real GBA START press at frame 1250, then captures
echo framebuffers at frames 1600 and 3000.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0S0_STAGE_C2.ps1"
exit /b %errorlevel%
