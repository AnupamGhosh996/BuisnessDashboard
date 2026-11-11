@echo off
echo ========================================================
echo       InsightIQ - React Vite Frontend Development
echo ========================================================
cd frontend
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)
echo Starting Vite Dev Server on http://localhost:5173 ...
call npm run dev
pause
