@echo off
title Isaac Future - Observation
pushd "%~dp0"
"%~dp0.venv\Scripts\python.exe" -m isaac_threrisaifuture.launcher %*
set "ISAAC_LAUNCH_EXIT=%ERRORLEVEL%"
popd
echo.
echo Observation launcher finished with exit code %ISAAC_LAUNCH_EXIT%.
pause
exit /b %ISAAC_LAUNCH_EXIT%
