@echo off
echo Arret des processus lances par start_dev_stack.bat ...

REM Ferme les consoles qui ont ces titres
for %%T in ("Django" "Celery worker" "Flower" "Redis") do (
  for /f "tokens=2 delims=," %%P in ('tasklist /v /fo csv ^| findstr /i %%~T') do (
    echo   -> Fermeture %%~T (PID %%P) ...
    taskkill /PID %%P /F >nul 2>&1
  )
)

echo Termine.
