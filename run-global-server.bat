@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if not exist "%~dp0launcher.config.bat" (
  echo [ERROR] launcher.config.bat is missing next to the launcher.
  pause
  exit /b 1
)
call "%~dp0launcher.config.bat"
if not defined PROJECT_DIR set "PROJECT_DIR=%~dp0"
if not defined SERVER_PORT set "SERVER_PORT=3000"
if not defined SERVER_HOST set "SERVER_HOST=127.0.0.1"
if not defined STARTUP_WAIT_SECONDS set "STARTUP_WAIT_SECONDS=60"
if not defined SERVER_COMMAND (
  echo [ERROR] SERVER_COMMAND is missing in launcher.config.bat.
  pause
  exit /b 1
)
if not exist "%PROJECT_DIR%" (
  echo [ERROR] Project directory does not exist: "%PROJECT_DIR%"
  pause
  exit /b 1
)
where cloudflared.exe >nul 2>&1
if errorlevel 1 (
  if exist "%~dp0cloudflared.exe" (
    set "CLOUDFLARED=%~dp0cloudflared.exe"
  ) else (
    echo [ERROR] cloudflared.exe not found. Install Cloudflare Tunnel CLI or place cloudflared.exe next to this file.
    echo See README.txt for prerequisites and security notes.
    pause
    exit /b 1
  )
) else (
  set "CLOUDFLARED=cloudflared.exe"
)
echo =====================================================
echo  Loder Store Management System - Public HTTPS Launcher
echo =====================================================
echo Local target: http://%SERVER_HOST%:%SERVER_PORT%
echo Starting application in another window...
start "Loder - Application Server" /D "%PROJECT_DIR%" cmd /k "%SERVER_COMMAND%"
echo Waiting for the server to respond (up to %STARTUP_WAIT_SECONDS% seconds)...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$hostName = $env:SERVER_HOST; $port = $env:SERVER_PORT; $wait = [int]$env:STARTUP_WAIT_SECONDS; $url='http://'+$hostName+':'+$port+'/'; $ready=$false; for($i=0;$i -lt $wait;$i++){ try { $r=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop; $ready=$true; break } catch { if($_.Exception.Response){$ready=$true; break}; Start-Sleep -Seconds 1 } }; if($ready){exit 0}else{exit 1}"
if errorlevel 1 (
  echo [ERROR] Server did not respond. Inspect the application window, port, and command.
  echo Tunnel was NOT started.
  pause
  exit /b 1
)
echo.
echo [OK] Application responded locally.
echo Starting temporary public HTTPS tunnel...
echo Read the https://...trycloudflare.com URL displayed below.
echo Keep this window and the application server window open.
echo Close both windows to stop publishing the application.
echo WARNING: Anyone with the URL may reach the system. Do not expose live customer data.
echo.
"%CLOUDFLARED%" tunnel --url "http://%SERVER_HOST%:%SERVER_PORT%" --no-autoupdate
set "RESULT=%ERRORLEVEL%"
echo Tunnel exited with code %RESULT%.
pause
exit /b %RESULT%
