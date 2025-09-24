# =======================
# Stop-DevStack.ps1 (compat 5.1, sans ternaire)
# =======================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "=== Arret pile dev : Django / Celery / Flower / Redis ===" -ForegroundColor Cyan

$PidFile = Join-Path $env:TEMP "nids-devstack.pids"
$me = $PID

# 1) Fenetres avec titre "Nids:*"
$targets = @()
$byTitle = @( Get-Process -ErrorAction SilentlyContinue | Where-Object {
  $_.Id -ne $me -and $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "Nids:*"
})
if ($byTitle.Count) { $targets += $byTitle }

# 2) Fallback : PIDs du fichier
if ($targets.Count -eq 0 -and (Test-Path $PidFile)) {
  Write-Host " -> Aucune fenetre via titre. Tentative via PID file ..."
  $pids = @( Get-Content $PidFile | Where-Object { $_ -match '^\d+$' } | ForEach-Object {[int]$_} )
  foreach ($id in $pids) {
    if ($id -ne $me) {
      $p = Get-Process -Id $id -ErrorAction SilentlyContinue
      if ($p) { $targets += @($p) }
    }
  }
}

# 3) Fallback : scan WMI/CommandLine (pwsh/powershell) + commandes du projet
if ($targets.Count -eq 0) {
  Write-Host " -> Tentative via WMI/CommandLine ..."
  $wmi = @( Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $me -and (
      ($_.Name -match '^(powershell|pwsh)(\.exe)?$' -and $_.CommandLine -match 'Nids:') -or
      $_.CommandLine -match 'observations_nids' -or
      $_.CommandLine -match 'manage\.py\s+runserver' -or
      $_.CommandLine -match 'celery\s+-A\s+observations_nids' -or
      $_.CommandLine -match '\bflower\b'
    )
  })
  foreach ($w in $wmi) {
    $p = Get-Process -Id $w.ProcessId -ErrorAction SilentlyContinue
    if ($p) { $targets += @($p) }
  }
}

# 4) Extinction (polie -> force arbre /T)
if ($targets.Count -gt 0) {
  foreach ($p in ($targets | Sort-Object Id -Unique)) {
    $title  = $p.MainWindowTitle
    $suffix = if ([string]::IsNullOrWhiteSpace($title)) { "" } else { " - '$title'" }
    Write-Host (" -> Extinction PID {0} ({1}){2} ..." -f $p.Id, $p.ProcessName, $suffix)

    try {
      if ($p.MainWindowHandle -ne 0) { $null = $p.CloseMainWindow(); Start-Sleep -Milliseconds 250 }
      if (-not $p.HasExited) {
        # tue le processus et ses enfants
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c","taskkill","/PID",$p.Id,"/T","/F" -NoNewWindow -Wait | Out-Null
      }
    } catch {}
  }
} else {
  Write-Host "Aucune fenetre/processus 'Nids' ou lies au projet trouves (titre/PID/CommandLine)."
}

# 5) Redis
$redis = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
if ($redis) {
  Write-Host " -> Arret Redis (PID $($redis.Id)) ..."
  try {
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c","taskkill","/PID",$redis.Id,"/F" -NoNewWindow -Wait | Out-Null
  } catch {}
} else {
  Write-Host "Redis ne semble pas tourner."
}

# 6) Nettoyage PID file
Remove-Item $PidFile -ErrorAction SilentlyContinue
Write-Host "Termine." -ForegroundColor Green
