@echo off
setlocal
title SoulGoldRecomp S0-C3 - Interactive Runtime
cls
echo ===============================================================
echo SoulGoldRecomp S0-C3 - Interactive Runtime
echo ===============================================================
echo.
echo S0-C2 title flow is sealed.
echo Toolfix11: WSL GUI probe uses printenv directly (no python quoting).
echo This stage opens the real SDL runtime for manual input/audio testing.
echo.
echo Controls:
echo   A=X    B=Z    Start=Enter    Select=RightShift
echo   D-pad=Arrow Keys             L=C   R=V
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0S0_STAGE_C3.ps1"
exit /b %errorlevel%
