@echo off
setlocal
title SoulGoldRecomp S0-B - Native Codegen and Runner Link
cls
echo ===============================================================
echo SoulGoldRecomp S0-B - Native Codegen and Runner Link
echo ===============================================================
echo.
echo S0-A must already be PASS.
echo This stage builds gba_recompile, emits SoulGold native shards,
echo and links the minimal SoulGoldRecomp runner.
echo.
echo If WSL build packages are missing, they will be installed.
echo sudo may ask for your WSL password once.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0S0_STAGE_B.ps1"
exit /b %errorlevel%
