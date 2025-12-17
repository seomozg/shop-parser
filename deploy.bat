@echo off
REM Shop Parser Deployment Script for Windows

echo 🚀 Starting Shop Parser deployment...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker first.
    pause
    exit /b 1
)

REM Check if docker-compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ docker-compose is not installed. Please install docker-compose first.
    pause
    exit /b 1
)

REM Create output directory if it doesn't exist
if not exist "output" mkdir output
if not exist "output\images" mkdir output\images

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Please create one with your DeepSeek API key.
    echo    Copy .env.example to .env and configure DEEPSEEK_API_KEY
    pause
    exit /b 1
)

REM Stop existing containers
echo 🛑 Stopping existing containers...
docker-compose down

REM Build and start containers
echo 🏗️  Building and starting containers...
docker-compose up -d --build

REM Wait for service to be ready
echo ⏳ Waiting for service to be ready...
timeout /t 10 /nobreak >nul

REM Check if service is running
curl -f http://localhost:5000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Deployment successful!
    echo 🌐 Web interface available at: http://localhost:5000
    echo 📊 Output files will be saved to: .\output\
) else (
    echo ❌ Service failed to start. Check logs with: docker-compose logs
    pause
    exit /b 1
)

echo.
echo 📋 Useful commands:
echo   View logs: docker-compose logs -f
echo   Stop service: docker-compose down
echo   Restart: docker-compose restart

pause
