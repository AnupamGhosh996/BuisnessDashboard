@echo off
set PYTHONHOME=C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0
set PYTHONPATH=%~dp0backend\runtime\DLLs;%~dp0backend
"%~dp0backend\runtime\python.exe" %*
