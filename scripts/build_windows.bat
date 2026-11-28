@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1"
if errorlevel 1 (
    echo.
    echo [ERROR] SpeedView.exe build failed.
    exit /b 1
)
echo.
echo [OK] Build complete. Output files are in dist\
endlocal
