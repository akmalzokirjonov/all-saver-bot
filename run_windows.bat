@echo off
title Allsaveruzbot - Build and Run
echo ===================================================
echo     Telegram Bot Installer and Runner (Windows)
echo ===================================================
echo.

:: 1. Check if Docker is installed
docker --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [X] ERROR: Docker Desktop is not installed or not running!
    echo.
    echo To easily run this bot without installing Python, Redis, FFmpeg,
    echo and Node.js manually, you MUST install Docker Desktop.
    echo.
    echo Download it here: https://www.docker.com/products/docker-desktop/
    echo Please install it, open Docker Desktop, and run this script again.
    echo.
    pause
    exit /b
)

:: 2. Check for .env file
IF NOT EXIST ".env" (
    echo [!] ALERT: .env file not found. Creating one from .env.example...
    copy .env.example .env >nul
    echo.
    echo [!] IMPORTANT: I am opening the .env file in Notepad.
    echo Please paste your Telegram Bot Token at "BOT_TOKEN=..."
    echo Save the file (Ctrl+S), close Notepad, and RUN THIS SCRIPT AGAIN.
    echo.
    start notepad .env
    pause
    exit /b
)

:: 3. Build and Run the containers
echo [*] Building and starting the bot in the background...
echo This might take a few minutes the very first time.
echo.
docker-compose up --build -d

echo.
echo ===================================================
echo [v] SUCCESS! The bot and Redis are now running!
echo ===================================================
echo.
echo - To view live logs:    docker-compose logs -f
echo - To stop the bot:      docker-compose down
echo.
pause
