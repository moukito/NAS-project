"""Module pour comparer deux fichiers de configuration de routeurs et générer un diff.\n\nCe module permet de comparer deux fichiers de configuration de routeurs similaires afin d'identifier\nles différences et faciliter l'implémentation de nouveaux protocoles.\n"""

import os
import re
from typing import Dict, List, Tuple, Set


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
            for section, lines in diff["added_sections"].items():
                f.write(f"### {section}\n```\n")
                for line in lines:
                    f.write(f"{line}\n")
                f.write("```\n\n")
        
        # Sections supprimées
        if diff["removed_sections"]:
            f.write("## Sections supprimées\n\n")
            for section, lines in diff["removed_sections"].items():
                f.write(f"### {section}\n```\n")
                for line in lines:
                    f.write(f"{line}\n")
                f.write("```\n\n")
        
        # Sections modifiées
        if diff["modified_sections"]:
            f.write("## Sections modifiées\n\n")
            for section, changes in diff["modified_sections"].items():
                f.write(f"### {section}\n")
                
                # Lignes ajoutées
                if changes.get("added"):
                    f.write("#### Lignes ajoutées\n```\n")
                    for line in changes["added"]:
                        f.write(f"{line}\n")
                    f.write("```\n\n")
                
                # Lignes supprimées
                if changes.get("removed"):
                    f.write("#### Lignes supprimées\n```\n")
                    for line in changes["removed"]:
                        f.write(f"{line}\n")
                    f.write("```\n\n")
        
    return output_file


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
    # Extraire les noms des routeurs à partir des noms de fichiers
    reference_name = os.path.basename(reference_config_file).split('_')[0]
    new_name = os.path.basename(new_config_file).split('_')[0]
    
    # Charger les configurations
    reference_config = load_config_file(reference_config_file)
    new_config = load_config_file(new_config_file)
    
    # Parser les configurations
    parsed_reference = parse_config(reference_config)
    parsed_new = parse_config(new_config)
    
    # Comparer les configurations
    diff = compare_configs(parsed_reference, parsed_new)
    
    # Sauvegarder le diff
    save_config_diff(diff, reference_name, new_name, output_dir)
    
    return diff


def main():
    """
    Fonction principale pour exécuter la comparaison de fichiers de configuration depuis la ligne de commande.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare deux fichiers de configuration de routeurs et génère un diff.")
    parser.add_argument("reference", help="Chemin vers le fichier de configuration du routeur de référence")
    parser.add_argument("new", help="Chemin vers le fichier de configuration du routeur avec les nouveaux protocoles")
    parser.add_argument("--output", "-o", default="diffs", help="Répertoire de sortie pour les fichiers de diff")
    
    args = parser.parse_args()
    
    print(f"Comparaison des configurations {args.reference} et {args.new}...")
    diff = compare_router_config_files(args.reference, args.new, args.output)
    
    # Afficher un résumé des différences
    print("\nRésumé des différences:")
    print(f"Sections ajoutées: {len(diff['added_sections'])}")
    print(f"Sections supprimées: {len(diff['removed_sections'])}")
    print(f"Sections modifiées: {len(diff['modified_sections'])}")


if __name__ == "__main__":
    main()