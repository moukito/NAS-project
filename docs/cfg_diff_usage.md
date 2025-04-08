# Guide d'utilisation de l'outil de comparaison de fichiers de configuration

Ce document explique comment utiliser les outils de comparaison de fichiers de configuration de routeurs (.cfg) développés dans le cadre du projet NAS.

## Introduction

Les outils de comparaison de fichiers de configuration permettent d'analyser les différences entre deux configurations de routeurs, en se concentrant sur les fichiers de configuration eux-mêmes plutôt que sur les commandes telnet. Cela facilite l'identification des changements apportés lors de l'implémentation de nouveaux protocoles ou de modifications de configuration.

## Outils disponibles

Plusieurs outils sont disponibles pour comparer les configurations des routeurs :

1. **cfg_diff.py** : Script principal pour comparer les fichiers de configuration
2. **compare_router_configs.py** : Module pour comparer deux configurations de routeurs
3. **config_diff_report.py** : Module pour générer un rapport HTML des différences
4. **router_config_diff.py** : Module de base pour la comparaison de configurations

## Utilisation de cfg_diff.py

Le script `cfg_diff.py` est le point d'entrée principal pour comparer les configurations des routeurs. Il offre plusieurs modes d'utilisation :

### Comparer deux fichiers de configuration

```bash
python code/cfg_diff.py files <fichier_reference> <fichier_nouveau> [options]
```

Options :
- `--output`, `-o` : Répertoire de sortie pour les fichiers de diff (par défaut : "diffs")
- `--format`, `-f` : Format du rapport ("text" ou "html", par défaut : "text")

Exemple :
```bash
python code/cfg_diff.py files configs/R1_config.txt configs/R2_config.txt --format html
```

### Comparer deux routeurs en cours d'exécution

```bash
python code/cfg_diff.py running <routeur_reference> <routeur_nouveau> [options]
```

Options :
- `--output`, `-o` : Répertoire de sortie pour les fichiers de diff (par défaut : "diffs")
- `--format`, `-f` : Format du rapport ("text" ou "html", par défaut : "text")

Exemple :
```bash
python code/cfg_diff.py running R1 R2 --format html
```

### Capturer la configuration d'un routeur

```bash
python code/cfg_diff.py capture <routeur> [options]
```

Options :
- `--output`, `-o` : Répertoire de sortie pour les fichiers de configuration (par défaut : "configs")

Exemple :
```bash
python code/cfg_diff.py capture R1
```

## Format des rapports de différences

### Rapport texte

Le rapport texte est structuré comme suit :

- **Sections ajoutées** : Sections présentes dans la nouvelle configuration mais pas dans la référence
- **Sections supprimées** : Sections présentes dans la configuration de référence mais pas dans la nouvelle
- **Sections modifiées** : Sections présentes dans les deux configurations mais avec des différences
  - **Lignes ajoutées** : Lignes ajoutées dans la section
  - **Lignes supprimées** : Lignes supprimées dans la section

### Rapport HTML

Le rapport HTML offre une visualisation plus claire des différences avec un code couleur :

- **Vert** : Sections ou lignes ajoutées
- **Rouge** : Sections ou lignes supprimées
- **Jaune** : Sections modifiées

## Exemples d'utilisation

### Exemple 1 : Comparer deux fichiers de configuration existants

```bash
python code/cfg_diff.py files format/exemple_config.cfg format/exemple_config_loopback.cfg --format html
```

Cette commande compare les deux fichiers de configuration et génère un rapport HTML des différences.

### Exemple 2 : Capturer et comparer deux routeurs en cours d'exécution

```bash
# Capturer les configurations
python code/cfg_diff.py capture R1
python code/cfg_diff.py capture R2

# Comparer les configurations capturées
python code/cfg_diff.py files configs/R1_config.txt configs/R2_config.txt
```

## Intégration avec d'autres outils

Les modules de comparaison de configurations peuvent être utilisés dans d'autres scripts Python :

```python
from compare_router_configs import compare_router_config_files
from config_diff_report import generate_config_diff_report

# Comparer deux fichiers de configuration
diff = compare_router_config_files("configs/R1_config.txt", "configs/R2_config.txt", "diffs")

# Générer un rapport HTML
html_file = generate_config_diff_report("configs/R1_config.txt", "configs/R2_config.txt", "diffs")
```

## Conclusion

Les outils de comparaison de fichiers de configuration facilitent l'analyse des différences entre deux configurations de routeurs, en se concentrant sur les fichiers de configuration eux-mêmes plutôt que sur les commandes telnet. Cela permet une meilleure compréhension des changements apportés et facilite l'implémentation de nouveaux protocoles.