# =======================$RedisCli     = "C:\Projets\Redis\redis-cli.exe"
# =======================
# Start-DevStack.ps1 (corrigé)
# =======================

# === CONFIG À ADAPTER ===
$ProjectDir   = "C:\Projets\observations_nids"
$VenvActivate = "$ProjectDir\.venv\Scripts\Activate.ps1"

# Chemin complet vers redis-server.exe (ex: C:\Redis\redis-server.exe)
$RedisExe     = "C:\Projets\Redis\redis-server.exe"
# (Optionnel) Chemin vers redis-cli.exe si tu veux tester un PING spécifique
$RedisCli     = "C:\Projets\Redis\redis-cli.exe"

# Réseau / Ports
$DjangoHost   = "127.0.0.1"
$DjangoPort   = 8000
$FlowerPort   = 5555

# Nom du module Celery (projet)
$CeleryApp    = "observations_nids"

$script:PidFile = Join-Path $env:TEMP "nids-devstack.pids"
# Réinitialiser le fichier PID à chaque démarrage
Set-Content -Path $script:PidFile -Value "" -Encoding ASCII -Force


# === FONCTIONS ===

function Wait-PortReady {
    param(
        [string]$TargetHost = "127.0.0.1",
        [int]$Port = 6379,
        [int]$TimeoutSec = 20
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    Write-Host "Attente que ${TargetHost}:$Port soit joignable (timeout ${TimeoutSec}s) ..."
    while ((Get-Date) -lt $deadline) {
        $ok = Test-NetConnection -ComputerName $TargetHost -Port $Port -InformationLevel Quiet
        if ($ok) { 
            Write-Host " -> Port $Port OK." -ForegroundColor Green
            return $true 
        }
        Start-Sleep -Seconds 1
    }
    Write-Warning " -> Port $Port non joignable après ${TimeoutSec}s."
    return $false
}

function Start-Window {
    param(
        [Parameter(Mandatory=$true)][string]$Title,
        [Parameter(Mandatory=$true)][string]$Command,
        [string]$WorkingDirectory = $ProjectDir
    )
    $full = @"
`$Host.UI.RawUI.WindowTitle = '$Title';
if (Test-Path '$VenvActivate') { . '$VenvActivate' };
$Command
"@

    # IMPORTANT: -PassThru pour récupérer l'objet Process et donc le PID
    $proc = Start-Process -FilePath "powershell.exe" `
        -ArgumentList "-NoLogo","-NoExit","-ExecutionPolicy","Bypass","-Command",$full `
        -WorkingDirectory $WorkingDirectory -PassThru

    # Enregistrer le PID pour l'arrêt
    if ($script:PidFile) { Add-Content -Path $script:PidFile -Value $proc.Id }

    return $proc
}


# === DÉBUT ===

Write-Host "=== Démarrage pile dev : Redis -> Django -> Celery -> Flower ===" -ForegroundColor Cyan

# 1) Redis
if (-not (Test-Path $RedisExe)) {
    Write-Error "redis-server introuvable : $RedisExe. Modifie `$RedisExe en haut du script."
    exit 1
}

$redisRunning = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
if ($redisRunning) {
    Write-Host "[1/4] Redis déjà démarré (PID: $($redisRunning.Id))."
} else {
    Write-Host "[1/4] Démarrage Redis..."
    Start-Process -FilePath $RedisExe -WorkingDirectory (Split-Path $RedisExe) | Out-Null
    # Attends que le port 6379 réponde
    Wait-PortReady -TargetHost "127.0.0.1" -Port 6379 -TimeoutSec 20 | Out-Null
}

# (Optionnel) Test PING via redis-cli si présent
if (Test-Path $RedisCli) {
    try {
        $pong = & $RedisCli -h 127.0.0.1 -p 6379 ping 2>$null
        if ($pong -ne "PONG") { Write-Warning "redis-cli ping n'a pas répondu PONG (réponse: '$pong')." }
        else { Write-Host "redis-cli ping -> PONG" -ForegroundColor Green }
    } catch { Write-Warning "redis-cli ping a échoué : $($_.Exception.Message)" }
}

# 2) Django
Write-Host "[2/4] Démarrage Django (http://${DjangoHost}:$DjangoPort) ..."
Start-Window -Title "Nids: Django" -Command "python manage.py runserver ${DjangoHost}:$DjangoPort"

# 3) Celery worker
Write-Host "[3/4] Démarrage Celery worker ..."
Start-Window -Title "Nids: Celery worker" -Command "celery -A $CeleryApp worker --loglevel=info --pool=eventlet"

# 4) Flower
Write-Host "[4/4] Démarrage Flower (http://127.0.0.1:$FlowerPort) ..."
Start-Window -Title "Nids: Flower" -Command "celery -A $CeleryApp flower --port=$FlowerPort --loglevel=info"

# Optionnel : ouvrir Flower dans le navigateur
Start-Process "http://127.0.0.1:$FlowerPort" | Out-Null

Write-Host ""
Write-Host "Tout est lancé :" -ForegroundColor Green
Write-Host " - Django  : http://${DjangoHost}:$DjangoPort"
Write-Host " - Flower  : http://127.0.0.1:$FlowerPort"
Write-Host ""
