# Outil de comparaison de configurations réseau

Cet outil permet de comparer deux réseaux quasi identiques afin de générer les commandes nécessaires pour implémenter des protocoles supplémentaires. Il est particulièrement utile pour identifier les différences entre un réseau de référence et un réseau avec des fonctionnalités additionnelles.

## Fonctionnalités

- Capture des configurations de routeurs via telnet
- Comparaison de deux fichiers d'intention réseau
- Comparaison de deux routeurs en cours d'exécution
- Génération de commandes telnet pour appliquer les différences
- Application automatique des différences aux routeurs

## Utilisation

### Capture de configurations

Pour capturer les configurations de tous les routeurs définis dans un fichier d'intention :

```bash
python code/capture_config.py format/exemple.json --output configs
```

### Comparaison de deux fichiers d'intention

Pour comparer deux fichiers d'intention et générer les commandes nécessaires pour passer de l'un à l'autre :

```bash
python code/compare_networks.py intent format/reference.json format/nouveau.json --output diffs
```

Pour appliquer automatiquement les différences aux routeurs :

```bash
python code/compare_networks.py intent format/reference.json format/nouveau.json --output diffs --apply
```

### Comparaison de deux routeurs en cours d'exécution

Pour comparer les configurations de deux routeurs en cours d'exécution :

```bash
python code/compare_networks.py running R1 R2 --output diffs
```

Pour appliquer les différences à un troisième routeur :

```bash
python code/compare_networks.py running R1 R2 --output diffs --apply R3
```

## Workflow recommandé

1. Créer un réseau de référence avec les fonctionnalités de base
2. Créer un second réseau avec les protocoles supplémentaires à implémenter
3. Utiliser l'outil de comparaison pour générer les commandes nécessaires
4. Vérifier les commandes générées
5. Appliquer les commandes au réseau de référence

## Structure des fichiers

- `capture_config.py` : Module pour capturer les configurations des routeurs
- `config_diff.py` : Module pour comparer deux configurations et générer un diff
- `compare_networks.py` : Module principal pour comparer deux réseaux

## Exemples de sorties

Les fichiers de diff générés contiennent les commandes telnet nécessaires pour transformer un routeur en un autre. Exemple :

```
# Commandes ajoutées pour R1
enable
configure terminal
ipv6 router ospf 1984
 redistribute connected
 redistribute static
exit
end
write memory
```

## Limitations

- L'outil ne gère pas la suppression de configurations existantes
- Les commandes générées doivent être vérifiées manuellement avant application en production
- Certaines configurations complexes peuvent nécessiter des ajustements manuels