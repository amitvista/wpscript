@echo off
echo ===================================================
echo Starting Brave with your logged-in profile for Automation...
echo ===================================================
taskkill /F /IM brave.exe >nul 2>&1
timeout /t 1 >nul
start "" "%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe" --remote-debugging-port=9555 --user-data-dir="%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data" https://mail.google.com
echo Done! Your logged-in Gmail is ready.
