"""Module pour comparer deux configurations de routeurs et générer un rapport de différences.

Ce module permet de comparer deux fichiers de configuration de routeurs (.cfg) afin d'identifier
les différences et générer un rapport détaillé, facilitant ainsi l'implémentation de nouveaux protocoles.
"""

import os
import re
from typing import Dict, List, Tuple, Set, Optional

from GNS3 import Connector
from capture_config import capture_router_config


def load_config_file(config_file: str) -> str:
    """
    Charge un fichier de configuration de routeur.
    
    Args:
        config_file (str): Chemin vers le fichier de configuration.
        
    Returns:
        str: Contenu du fichier de configuration.
    """
    try:
        with open(config_file, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Erreur lors du chargement du fichier {config_file}: {e}")
        return ""


def extract_hostname(config: str) -> str:
    """
    Extrait le nom d'hôte d'une configuration de routeur.
    
    Args:
        config (str): Configuration du routeur.
        
    Returns:
        str: Nom d'hôte du routeur.
    """
    hostname_pattern = re.compile(r'^hostname (\S+)', re.MULTILINE)
    match = hostname_pattern.search(config)
    if match:
        return match.group(1)
    return "unknown"


def parse_config(config: str) -> Dict[str, List[str]]:
    """
    Parse la configuration d'un routeur en sections.
    
    Args:
        config (str): Configuration du routeur.
        
    Returns:
        Dict[str, List[str]]: Dictionnaire des sections de configuration.
    """
    sections = {}
    current_section = "global"
    sections[current_section] = []
    
    # Expressions régulières pour identifier les débuts de section
    interface_pattern = re.compile(r'^interface (\S+)')
    router_pattern = re.compile(r'^router (\S+) (\S+)')
    route_map_pattern = re.compile(r'^route-map (\S+)')
    ipv6_pattern = re.compile(r'^ipv6 router (\S+) (\S+)')
    acl_pattern = re.compile(r'^ip access-list (\S+) (\S+)')
    
    for line in config.split('\n'):
        line = line.strip()
        
        # Ignorer les lignes vides et les commentaires
        if not line or line.startswith('!'):
            continue
            
        # Vérifier si c'est le début d'une nouvelle section
        interface_match = interface_pattern.match(line)
        router_match = router_pattern.match(line)
        route_map_match = route_map_pattern.match(line)
        ipv6_match = ipv6_pattern.match(line)
        acl_match = acl_pattern.match(line)
        
        if interface_match:
            current_section = f"interface_{interface_match.group(1)}"
            sections[current_section] = [line]
        elif router_match:
            protocol = router_match.group(1)
            process_id = router_match.group(2)
            current_section = f"{protocol}_{process_id}"
            sections[current_section] = [line]
        elif ipv6_match:
            protocol = ipv6_match.group(1)
            process_id = ipv6_match.group(2)
            current_section = f"ipv6_{protocol}_{process_id}"
            sections[current_section] = [line]
        elif route_map_match:
            route_map_name = route_map_match.group(1)
            current_section = f"route_map_{route_map_name}"
            sections[current_section] = [line]
        elif acl_match:
            acl_type = acl_match.group(1)
            acl_name = acl_match.group(2)
            current_section = f"acl_{acl_type}_{acl_name}"
            sections[current_section] = [line]
        elif line == "end" or line == "exit":
            current_section = "global"
        else:
            sections[current_section].append(line)
            
    return sections


def compare_configs(reference_config: Dict[str, List[str]], new_config: Dict[str, List[str]]) -> Dict[str, Dict[str, List[str]]]:
    """
    Compare deux configurations et génère un diff.
    
    Args:
        reference_config (Dict[str, List[str]]): Configuration de référence.
        new_config (Dict[str, List[str]]): Nouvelle configuration.
        
    Returns:
        Dict[str, Dict[str, List[str]]]: Différences entre les configurations.
    """
    diff = {
        "added_sections": {},
        "removed_sections": {},
        "modified_sections": {}
    }
    
    # Trouver les sections ajoutées
    for section in new_config:
        if section not in reference_config:
            diff["added_sections"][section] = new_config[section]
    
    # Trouver les sections supprimées
    for section in reference_config:
        if section not in new_config:
            diff["removed_sections"][section] = reference_config[section]
    
    # Trouver les sections modifiées
    for section in reference_config:
        if section in new_config:
            ref_lines = set(reference_config[section])
            new_lines = set(new_config[section])
            
            added_lines = new_lines - ref_lines
            removed_lines = ref_lines - new_lines
            
            if added_lines or removed_lines:
                diff["modified_sections"][section] = {
                    "added": list(added_lines),
                    "removed": list(removed_lines)
                }
    
    return diff


def save_config_diff(diff: Dict[str, Dict[str, List[str]]], reference_name: str, new_name: str, output_dir: str = "diffs") -> str:
    """
    Sauvegarde les différences entre deux configurations dans un fichier.
    
    Args:
        diff (Dict[str, Dict[str, List[str]]]): Différences entre les configurations.
        reference_name (str): Nom du routeur de référence.
        new_name (str): Nom du routeur avec les nouveaux protocoles.
        output_dir (str): Répertoire de sortie pour les fichiers de diff.
        
    Returns:
        str: Chemin du fichier de diff créé.
    """
    # Créer le répertoire de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Créer le chemin du fichier de sortie
    output_file = os.path.join(output_dir, f"{reference_name}_to_{new_name}_diff.txt")
    
    # Écrire le diff dans le fichier
    with open(output_file, 'w') as f:
        f.write(f"# Différences de configuration entre {reference_name} et {new_name}\n\n")
        
        # Sections ajoutées
        if diff["added_sections"]:
            f.write("## Sections ajoutées\n\n")
            for section, lines in sorted(diff["added_sections"].items()):
                f.write(f"### {section}\n```\n")
                for line in lines:
                    f.write(f"{line}\n")
                f.write("```\n\n")
        
        # Sections supprimées
        if diff["removed_sections"]:
            f.write("## Sections supprimées\n\n")
            for section, lines in sorted(diff["removed_sections"].items()):
                f.write(f"### {section}\n```\n")
                for line in lines:
                    f.write(f"{line}\n")
                f.write("```\n\n")
        
        # Sections modifiées
        if diff["modified_sections"]:
            f.write("## Sections modifiées\n\n")
            for section, changes in sorted(diff["modified_sections"].items()):
                f.write(f"### {section}\n")
                
                # Lignes ajoutées
                if changes.get("added"):
                    f.write("#### Lignes ajoutées\n```\n")
                    for line in sorted(changes["added"]):
                        f.write(f"{line}\n")
                    f.write("```\n\n")
                
                # Lignes supprimées
                if changes.get("removed"):
                    f.write("#### Lignes supprimées\n```\n")
                    for line in sorted(changes["removed"]):
                        f.write(f"{line}\n")
                    f.write("```\n\n")
        
    print(f"Diff écrit dans {output_file}")
    return output_file


def compare_router_config_files(reference_config_file: str, new_config_file: str, output_dir: str = "diffs") -> Dict[str, Dict[str, List[str]]]:
    """
    Compare deux fichiers de configuration de routeurs et génère un diff.
    
    Args:
        reference_config_file (str): Chemin vers le fichier de configuration du routeur de référence.
        new_config_file (str): Chemin vers le fichier de configuration du routeur avec les nouveaux protocoles.
        output_dir (str): Répertoire de sortie pour les fichiers de diff.
        
    Returns:
        Dict[str, Dict[str, List[str]]]: Différences entre les configurations.
    """
    # Charger les configurations
    reference_config = load_config_file(reference_config_file)
    new_config = load_config_file(new_config_file)
    
    # Extraire les noms des routeurs
    reference_name = extract_hostname(reference_config) or os.path.basename(reference_config_file).split('_')[0]
    new_name = extract_hostname(new_config) or os.path.basename(new_config_file).split('_')[0]
    
    # Parser les configurations
    parsed_reference = parse_config(reference_config)
    parsed_new = parse_config(new_config)
    
    # Comparer les configurations
    diff = compare_configs(parsed_reference, parsed_new)
    
    # Sauvegarder le diff
    save_config_diff(diff, reference_name, new_name, output_dir)
    
    return diff


def compare_running_configs(reference_router: str, new_router: str, connector: Connector, output_dir: str = "diffs") -> Dict[str, Dict[str, List[str]]]:
    """
    Compare les configurations en cours d'exécution de deux routeurs et génère un diff.
    
    Args:
        reference_router (str): Nom du routeur de référence.
        new_router (str): Nom du routeur avec les nouveaux protocoles.
        connector (Connector): Connecteur GNS3.
        output_dir (str): Répertoire de sortie pour les fichiers de diff.
        
    Returns:
        Dict[str, Dict[str, List[str]]]: Différences entre les configurations.
    """
    # Capturer les configurations des routeurs
    reference_config_file = capture_router_config(connector, reference_router, "configs")
    new_config_file = capture_router_config(connector, new_router, "configs")
    
    # Comparer les configurations
    return compare_router_config_files(reference_config_file, new_config_file, output_dir)


def main():
    """
    Fonction principale pour exécuter la comparaison de fichiers de configuration depuis la ligne de commande.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare deux fichiers de configuration de routeurs et génère un diff.")
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Sous-commande pour comparer deux fichiers de configuration
    file_parser = subparsers.add_parser("files", help="Compare deux fichiers de configuration")
    file_parser.add_argument("reference", help="Chemin vers le fichier de configuration du routeur de référence")
    file_parser.add_argument("new", help="Chemin vers le fichier de configuration du routeur avec les nouveaux protocoles")
    file_parser.add_argument("--output", "-o", default="diffs", help="Répertoire de sortie pour les fichiers de diff")
    
    # Sous-commande pour comparer deux routeurs en cours d'exécution
    running_parser = subparsers.add_parser("running", help="Compare deux routeurs en cours d'exécution")
    running_parser.add_argument("reference", help="Nom du routeur de référence")
    running_parser.add_argument("new", help="Nom du routeur avec les nouveaux protocoles")
    running_parser.add_argument("--output", "-o", default="diffs", help="Répertoire de sortie pour les fichiers de diff")
    
    args = parser.parse_args()
    
    if args.command == "files":
        print(f"Comparaison des configurations {args.reference} et {args.new}...")
        diff = compare_router_config_files(args.reference, args.new, args.output)
    
    elif args.command == "running":
        print(f"Comparaison des configurations en cours d'exécution de {args.reference} et {args.new}...")
        connector = Connector()
        diff = compare_running_configs(args.reference, args.new, connector, args.output)
    
    else:
        parser.print_help()
        return
    
    # Afficher un résumé des différences
    print("\nRésumé des différences:")
    print(f"Sections ajoutées: {len(diff['added_sections'])}")
    print(f"Sections supprimées: {len(diff['removed_sections'])}")
    print(f"Sections modifiées: {len(diff['modified_sections'])}")


if __name__ == "__main__":
    main()