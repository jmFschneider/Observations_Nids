# 1. Définir le dossier à analyser
$dossierRacine = "."

Write-Host "Analyse en cours (exclusion des dossiers '.*' et 'node_modules')..." -ForegroundColor Cyan

# 2. Récupérer les fichiers .js avec le nouveau filtre
# Le filtre regex "[\\/]\." détecte un slash ou backslash suivi d'un point
$fichiersJS = Get-ChildItem -Path $dossierRacine -Recurse -Filter "*.js" | 
              Where-Object { 
                ($_.FullName -notmatch "node_modules") -and 
                ($_.FullName -notmatch "[\\/]\.") -and 
                ($_.FullName -notmatch "staticfiles") 
              }

# 3. Traitement des résultats
$resultats = @()
$totalLignesGlobal = 0

foreach ($fichier in $fichiersJS) {
    # On force la lecture en UTF8 pour éviter les erreurs de lecture, et on gère les erreurs d'accès
    try {
        $nbLignes = (Get-Content $fichier.FullName -ErrorAction Stop | Measure-Object -Line).Lines
    }
    catch {
        $nbLignes = 0 # En cas de fichier illisible ou verrouillé
    }
    
    $totalLignesGlobal += $nbLignes

    $infoFichier = [PSCustomObject]@{
        "Nom du Fichier" = $fichier.Name
        "Localisation"   = $fichier.DirectoryName
        "Nbre de Lignes" = $nbLignes
    }
    
    $resultats += $infoFichier
}

# 4. Affichage du tableau trié
# On coupe le chemin de localisation pour qu'il ne soit pas trop long à l'affichage
$resultats | Sort-Object "Nbre de Lignes" -Descending | Select-Object "Nom du Fichier", "Nbre de Lignes", "Localisation" | Format-Table -AutoSize

# 5. Résumé
Write-Host "------------------------------------------------"
Write-Host "RÉSUMÉ FINAL" -ForegroundColor Yellow
Write-Host "Fichiers analysés : $($resultats.Count)"
Write-Host "Total lignes de code : $totalLignesGlobal"
Write-Host "------------------------------------------------"