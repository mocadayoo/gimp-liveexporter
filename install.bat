@echo off
setlocal

powershell.exe -NoProfile -File "%~dp0tools\install.ps1"
set "exitCode=%ERRORLEVEL%"

if not "%exitCode%"=="0" (
    echo.
    echo Installation failed. See the message above.
)

echo.
pause
exit /b %exitCode%
