# Script PowerShell pour exécuter des commandes Python

# Liste des paires de routeurs à comparer
$routeurs = @(
    @("R1", "PE1"),
    @("R2", "PE2"),
    @("R3", "P1"),
    @("R4", "P2"),
    @("R5", "CE1"),
    @("R6", "CE2")
)

# Répertoire de sortie pour les rapports
$outputDir = "diffs"

# Format du rapport
$format = "html"

# Exécution des commandes
foreach ($pair in $routeurs) {
    $routeur1 = $pair[0]
    $routeur2 = $pair[1]
    $command = "python code/cfg_diff.py running $routeur1 $routeur2 --format $format"
    Write-Host "Exécution de la commande : $command"
    Invoke-Expression $command
}