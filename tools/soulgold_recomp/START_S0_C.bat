@echo off
setlocal
title SoulGoldRecomp S0-C - Headless Runtime Evidence
cls
echo ===============================================================
echo SoulGoldRecomp S0-C - Headless Runtime Evidence
echo ===============================================================
echo.
echo S0-A and S0-B must already be PASS.
echo This stage verifies the exact runner/ROM/BIOS, runs 1200 frames
echo headlessly with BIOS HLE boot, and captures framebuffer/coverage.
echo.
echo If your verified GBA BIOS is not already in WSL, a Windows file
echo picker will open once. Select your own legally obtained gba_bios.bin.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0S0_STAGE_C.ps1"
exit /b %errorlevel%
