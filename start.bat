@echo off
REM One-click start for the Rythu Mitra prototype (Windows).
REM First run installs everything; later runs just start the server.
cd /d "%~dp0"

if not exist backend\.venv (
  echo Setting up Python environment...
  python -m venv backend\.venv || goto :error
  backend\.venv\Scripts\python -m pip install -r backend\requirements.txt || goto :error
)
if not exist frontend\node_modules (
  echo Installing frontend packages...
  pushd frontend && call npm install && popd
)
if not exist frontend\dist (
  echo Building frontend...
  pushd frontend && call npm run build && popd
)

echo.
echo  Rythu Mitra is running at http://localhost:8000  (press Ctrl+C to stop)
echo.
start "" http://localhost:8000
backend\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --port 8000
goto :eof

:error
echo Setup failed. Make sure Python 3.10+ and Node.js 18+ are installed.
pause
