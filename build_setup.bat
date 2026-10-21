@echo off
powershell -NoProfile -File "%~dp0build_setup.ps1"
exit /b %ERRORLEVEL%
