@echo off
echo ========================================================
echo       InsightIQ - AI Business Intelligence Platform
echo ========================================================
echo Starting Backend Server on http://localhost:8000 ...

set PYTHONHOME=C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0
set PYTHONPATH=%~dp0backend\runtime\DLLs;%~dp0backend;%~dp0

if exist "%~dp0backend\runtime\python.exe" (
    "%~dp0backend\runtime\python.exe" server.py 8000
) else (
    python server.py 8000
)
pause
