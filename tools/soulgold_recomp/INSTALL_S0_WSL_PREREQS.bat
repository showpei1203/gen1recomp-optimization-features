@echo off
setlocal
title SoulGoldRecomp S0 - WSL Prerequisite Installer
cls
echo ===============================================================
echo SoulGoldRecomp S0 - WSL Prerequisite Installer
echo ===============================================================
echo.
echo This installs the official SoulGold / pokeemerald-expansion
echo WSL build prerequisites, then reruns S0-A.
echo.
echo If sudo asks for your Linux/WSL password:
echo   - type the password and press Enter
echo   - NOTHING will appear while you type; that is normal
echo.
pause

echo.
echo [1/4] Checking WSL...
wsl.exe --status >nul 2>&1
if errorlevel 1 (
    echo ERROR: WSL is not available.
    goto :fail
)

echo.
echo [2/4] Updating Ubuntu/Debian package index...
wsl.exe sudo apt-get update
if errorlevel 1 (
    echo.
    echo ERROR: apt-get update failed.
    echo If this was a password error, rerun this installer and enter your WSL password.
    goto :fail
)

echo.
echo [3/4] Installing SoulGold build prerequisites...
wsl.exe sudo apt-get install -y build-essential binutils-arm-none-eabi gcc-arm-none-eabi libnewlib-arm-none-eabi git libpng-dev python3
if errorlevel 1 (
    echo.
    echo ERROR: prerequisite installation failed.
    goto :fail
)

echo.
echo [4/4] Verifying tools...
wsl.exe make --version
if errorlevel 1 goto :verifyfail
wsl.exe python3 --version
if errorlevel 1 goto :verifyfail
wsl.exe git --version
if errorlevel 1 goto :verifyfail
wsl.exe arm-none-eabi-gcc --version
if errorlevel 1 goto :verifyfail
wsl.exe arm-none-eabi-readelf --version
if errorlevel 1 goto :verifyfail

echo.
echo ===============================================================
echo PREREQUISITES PASS
echo ===============================================================
echo.
echo Starting S0-A now...
echo.
call "%~dp0START_S0_A.bat"
exit /b %errorlevel%

:verifyfail
echo.
echo ERROR: Packages installed, but one or more required tools are still unavailable.
goto :fail

:fail
echo.
echo Nothing in the SoulGold project was promoted.
echo Take a screenshot of this window and return it.
pause
exit /b 1
