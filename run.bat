@echo off
rem Data Explorer: start the app on this computer (Windows). Usage: run
rem Installs uv if needed (no admin rights), which fetches Python and the libraries on first run.
setlocal
cd /d "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
    if not exist "%USERPROFILE%\.local\bin\uv.exe" (
        echo Installing uv, first run only...
        powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    )
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

echo Preparing Data Explorer, the first run downloads the libraries (a few minutes)...
uv run --project backend --frozen --no-dev python backend\launch.py %*
