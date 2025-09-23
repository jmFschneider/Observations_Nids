@echo off
setlocal ENABLEDELAYEDEXPANSION

REM === CONFIG A ADAPTER ===  start "Redis" cmd /k "C:\Redis\redis-server.exe"
set "PROJECT_DIR=C:\Projets\observations_nids"
set "VENV=%PROJECT_DIR%\.venv"
set "DJANGO_HOST=127.0.0.1"
set "DJANGO_PORT=8000"
set "FLOWER_PORT=5555"

REM === NE RIEN CHANGER APRES CETTE LIGNE (sauf si tu sais ce que tu fais) ===
cd /d "%PROJECT_DIR%"

REM Active le venv dans cette fenêtre (utile si tu lances sans sous-fenêtres)
if exist "%VENV%\Scripts\activate.bat" call "%VENV%\Scripts\activate.bat"

echo.
echo [1/4] Verif / Demarrage REDIS...
where redis-cli >nul 2>&1
if %ERRORLEVEL%==0 (
  redis-cli -h 127.0.0.1 -p 6379 ping >nul 2>&1
  if %ERRORLEVEL%==0 (
    echo     Redis est deja demarre.
  ) else (
    echo     Redis n'est pas demarre -> lancement...
    start "Redis" cmd /k "redis-server"
    timeout /t 3 >nul
  )
) else (
  echo     redis-cli introuvable -> on tente de lancer redis-server...
  start "Redis" cmd /k "C:\Projets\Redis\redis-server.exe"
  timeout /t 3 >nul
)

echo.
echo [2/4] Demarrage du serveur Django...
start "Django" cmd /k "cd /d %PROJECT_DIR% && call %VENV%\Scripts\activate.bat && python manage.py runserver %DJANGO_HOST%:%DJANGO_PORT%"

echo.
echo [3/4] Demarrage du worker Celery...
start "Celery worker" cmd /k "cd /d %PROJECT_DIR% && call %VENV%\Scripts\activate.bat && celery -A observations_nids worker --loglevel=info --pool=eventlet"

echo.
echo [4/4] Demarrage de Flower (supervision)...
start "Flower" cmd /k "cd /d %PROJECT_DIR% && call %VENV%\Scripts\activate.bat && celery -A observations_nids flower --port=%FLOWER_PORT% --loglevel=info"

echo.
echo Tout est lance.
echo - Django  : http://%DJANGO_HOST%:%DJANGO_PORT%
echo - Flower  : http://127.0.0.1:%FLOWER_PORT%
echo.
endlocal
