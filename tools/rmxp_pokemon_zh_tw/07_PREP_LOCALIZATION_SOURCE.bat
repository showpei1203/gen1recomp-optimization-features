@echo off
setlocal
if "%~1"=="" (
  echo.
  echo Drag the Pokemon Essentials game ZIP onto this BAT file.
  echo It will create a smaller *_LOCALIZATION_SOURCE.zip next to the original ZIP.
  echo.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0toolchain\prep_localization_source.ps1" -ZipPath "%~1"
echo.
pause
