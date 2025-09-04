@echo off
REM Script để chạy SonarQube scan trên Windows

REM Load environment variables từ file .env
if exist ".env" (
    echo Loading environment variables from .env file...
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
) else (
    echo Warning: .env file not found
)

if "%SONAR_TOKEN%"=="" (
    echo Error: SONAR_TOKEN environment variable is not set
    echo Please create .env file with: SONAR_TOKEN=your_token_here
    pause
    exit /b 1
)

if "%1"=="" (
    echo Usage: run_scan.bat ^<project_directory^>
    echo Example: run_scan.bat C:\path\to\your\project
    pause
    exit /b 1
)

set PROJECT_DIR=%1
set PROJECT_KEY=my-service

echo Starting SonarQube scan for project: %PROJECT_DIR%
echo Project Key: %PROJECT_KEY%
echo.

REM Tự động phát hiện source directory
set SOURCE_DIR=.
if exist "%PROJECT_DIR%\src" set SOURCE_DIR=src
if exist "%PROJECT_DIR%\source" set SOURCE_DIR=source
if exist "%PROJECT_DIR%\app" set SOURCE_DIR=app

REM Tạo sonar-project.properties trong thư mục project
echo sonar.projectKey=%PROJECT_KEY% > "%PROJECT_DIR%\sonar-project.properties"
echo sonar.projectName=%PROJECT_KEY% >> "%PROJECT_DIR%\sonar-project.properties"
echo sonar.sources=%SOURCE_DIR% >> "%PROJECT_DIR%\sonar-project.properties"
echo sonar.exclusions=**/node_modules/**,**/dist/**,**/build/**,**/.git/** >> "%PROJECT_DIR%\sonar-project.properties"

echo Using source directory: %SOURCE_DIR%

echo Created sonar-project.properties in %PROJECT_DIR%
echo.

REM Chạy scan bằng Docker container có sẵn
echo Running SonarQube scan...
echo Using token: %SONAR_TOKEN:~0,10%...

REM Khởi động sonar-scanner container nếu chưa chạy
docker start sonar_scanner 2>nul || (
    echo Starting sonar-scanner container...
    docker-compose --profile tools up -d sonar-scanner
    timeout /t 3 >nul
)

REM Chạy scan trong container có sẵn
docker exec -w /usr/src ^
  -e SONAR_HOST_URL="http://sonarqube:9000" ^
  -e SONAR_TOKEN="%SONAR_TOKEN%" ^
  sonar_scanner sonar-scanner

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Scan completed successfully!
    echo Wait a few seconds for background processing, then run:
    echo python export_issues.py %PROJECT_KEY%
) else (
    echo.
    echo Scan failed with error code %ERRORLEVEL%
)

pause