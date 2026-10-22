@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Project Python is missing; run the documented project setup.
    exit /b 2
)
pushd "%~dp0"
"%~dp0.venv\Scripts\python.exe" -m isaac_threrisaifuture.launcher --samples 1 --reconnects 0 --duration 180 --connection-timeout 180 --entry-mode continue %*
set "ISAAC_AGENT_EXIT=%ERRORLEVEL%"
popd
exit /b %ISAAC_AGENT_EXIT%
