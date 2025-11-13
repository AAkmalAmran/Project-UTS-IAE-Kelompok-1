@echo off
echo ========================================
echo Docker: Initialize All Databases
echo ========================================
echo.

echo Checking .env files...
if not exist service-1-route\.env (
    echo Creating service-1-route/.env...
    copy service-1-route\.env.example service-1-route\.env
)
if not exist service-2-stop\.env (
    echo Creating service-2-stop/.env...
    copy service-2-stop\.env.example service-2-stop\.env
)
if not exist service-3-bus\.env (
    echo Creating service-3-bus/.env...
    copy service-3-bus\.env.example service-3-bus\.env
)
if not exist service-4-schedule\.env (
    echo Creating service-4-schedule/.env...
    copy service-4-schedule\.env.example service-4-schedule\.env
)
echo .env files ready!
echo.

echo Creating instance folders...
if not exist service-1-route\instance mkdir service-1-route\instance
if not exist service-2-stop\instance mkdir service-2-stop\instance
if not exist service-3-bus\instance mkdir service-3-bus\instance
if not exist service-4-schedule\instance mkdir service-4-schedule\instance
echo Instance folders created!
echo.

echo Building Docker images...
docker-compose build
echo.

echo ========================================
echo Initializing Databases
echo ========================================
echo.

echo [1/4] Route Service Database...
docker-compose run --rm service-1-route flask init-db
docker-compose run --rm service-1-route flask seed-routes
echo Route Service: DONE
echo.

echo [2/4] Stop Service Database...
docker-compose run --rm service-2-stop flask init-db
docker-compose run --rm service-2-stop flask seed-stops
echo Stop Service: DONE
echo.

echo [3/4] Bus Service Database...
docker-compose run --rm service-3-bus flask init-db
docker-compose run --rm service-3-bus flask seed-buses
echo Bus Service: DONE
echo.

echo [4/4] Schedule Service Database...
docker-compose run --rm service-4-schedule flask init-db
docker-compose run --rm service-4-schedule flask seed-schedules
echo Schedule Service: DONE
echo.

echo ========================================
echo All Databases Initialized Successfully!
echo ========================================
echo.
echo Database files created:
dir /b service-1-route\instance\*.db 2>nul
dir /b service-2-stop\instance\*.db 2>nul
dir /b service-3-bus\instance\*.db 2>nul
dir /b service-4-schedule\instance\*.db 2>nul
echo.
echo Next step: docker-compose up -d
echo.
pause
