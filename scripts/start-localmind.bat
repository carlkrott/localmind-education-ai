@echo off
REM LocalMind — Windows startup script
REM Run this to start all LocalMind services

echo.
echo =========================================
echo   LocalMind — AI Education Companion
echo =========================================
echo.

cd /d "%~dp0.."

REM Check if Docker is available
docker ps >nul 2>&1
if errorlevel 1 (
    echo Docker Desktop is not running.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo Starting LocalMind stack...
docker compose up -d

echo.
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

docker compose ps

echo.
echo =========================================
echo LocalMind is running!
echo.
echo Services:
echo   AI Model:  http://localhost:8080
echo   Search:    http://localhost:8888
echo   Kiwix:     http://localhost:9090
echo.
echo Your Telegram bot is ready to use.
echo =========================================
echo.
