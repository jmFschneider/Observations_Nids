# =======================
# Start-DevStack.ps1 (Version 4 Zones - Couleurs Personnalisées)
# =======================

# === CONFIG ===
$ProjectDir   = "C:\Projets\observations_nids"
$VenvActivate = "$ProjectDir\.venv\Scripts\Activate.ps1"
$RedisExe     = "C:\Programmes non installes\Redis\redis-server.exe"
$DjangoHost   = "127.0.0.1"
$DjangoPort   = 8000
$FlowerPort   = 5555
$CeleryApp    = "observations_nids"

Write-Host "=== Démarrage de la pile Dev (Zones Colorées) ===" -ForegroundColor Cyan

# Fonction pour encoder une commande PowerShell en Base64 avec couleur
function Get-EncodedCmd {
    param($Title, $Script, $Color)
    $FullScript = @"
`$Host.UI.RawUI.WindowTitle = '$Title'
`$Host.UI.RawUI.ForegroundColor = '$Color'
Clear-Host
if (Test-Path '$VenvActivate') { . '$VenvActivate' }
cd '$ProjectDir'
$Script
"@
    $Bytes = [System.Text.Encoding]::Unicode.GetBytes($FullScript)
    return [Convert]::ToBase64String($Bytes)
}

# Préparation des commandes avec couleurs
$E1 = Get-EncodedCmd "Nids: Django" "python manage.py runserver ${DjangoHost}:${DjangoPort}" "Green"
$E2 = Get-EncodedCmd "Nids: Celery" "celery -A $CeleryApp worker --loglevel=info --pool=solo -Q celery,ocr" "Cyan"
$E3 = Get-EncodedCmd "Nids: Flower" "celery -A $CeleryApp flower --port=$FlowerPort" "Yellow"
$E4 = Get-EncodedCmd "Nids: Redis" "if (-not (Get-Process 'redis-server' -ErrorAction SilentlyContinue)) { cd (Split-Path '$RedisExe'); & '$RedisExe' } else { Write-Host 'Redis OK' -ForegroundColor Green }" "White"

# Construction de la commande pour Windows Terminal
$WT_Args = "new-tab -d `"$ProjectDir`" powershell.exe -NoExit -EncodedCommand $E1 ; " +
          "split-pane -V -d `"$ProjectDir`" powershell.exe -NoExit -EncodedCommand $E2 ; " +
          "move-focus left ; " +
          "split-pane -H -d `"$ProjectDir`" powershell.exe -NoExit -EncodedCommand $E3 ; " +
          "move-focus right ; " +
          "split-pane -H -d `"$ProjectDir`" powershell.exe -NoExit -EncodedCommand $E4"

Write-Host "Lancement de Windows Terminal en couleurs..." -ForegroundColor Yellow
Start-Process "wt.exe" -ArgumentList $WT_Args

# Ouvrir Flower
Start-Sleep -Seconds 5
Start-Process "http://127.0.0.1:$FlowerPort" | Out-Null