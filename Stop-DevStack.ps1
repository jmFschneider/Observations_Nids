# =======================
# Stop-DevStack.ps1
# =======================

Write-Host "=== Arrêt pile dev : Django / Celery / Flower / Redis ===" -ForegroundColor Cyan

# 1) Fermer les fenêtres PowerShell nommées "Nids: ..."
$targets = Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "Nids:*"
}

if ($targets) {
    foreach ($p in $targets) {
        Write-Host " -> Fermeture fenêtre '$($p.MainWindowTitle)' (PID $($p.Id)) ..."
        try {
            $p.CloseMainWindow() | Out-Null
            Start-Sleep -Milliseconds 300
            if (!$p.HasExited) { $p | Stop-Process -Force }
        } catch { }
    }
} else {
    Write-Host "Aucune fenêtre 'Nids:' trouvée."
}

# 2) Tenter d'arrêter Redis
$redis = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
if ($redis) {
    Write-Host " -> Arrêt Redis (PID $($redis.Id)) ..."
    try { $redis | Stop-Process -Force } catch { }
} else {
    Write-Host "Redis ne semble pas tourner."
}

Write-Host "Terminé." -ForegroundColor Green
