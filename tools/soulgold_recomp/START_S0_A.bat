@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo  SoulGoldRecomp S0-A - Source / Symbol / Runner Preparation
echo ============================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0S0_STAGE_A.ps1"
set RC=%ERRORLEVEL%
echo.
echo S0_STAGE_A_EXIT=%RC%
if not "%RC%"=="0" (
  echo Please return the log path printed above.
)
pause
exit /b %RC%
