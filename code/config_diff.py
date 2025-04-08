"""Module pour comparer deux configurations réseau et générer un diff.

Ce module permet de comparer deux configurations réseau similaires afin d'identifier
les différences et faciliter l'implémentation de nouveaux protocoles.
"""

import os
import re
from typing import Dict, List, Tuple, Set

from GNS3 import Connector
from writer import get_all_telnet_commands
from loadTelnetCommands import load_file


def get_router_config(connector: Connector, router_name: str) -> str:
    """
    Récupère la configuration actuelle d'un routeur via telnet.
    
    Args:
        connector (Connector): Connecteur GNS3 pour communiquer avec les nœuds.
        router_name (str): Nom du routeur dont on veut récupérer la configuration.
        
    Returns:
        str: Configuration complète du routeur.
    """
    try:
        # Établir une connexion telnet avec le routeur
        connector.telnet_connection(router_name)
        
        # Envoyer la commande "show running-config"
        output = connector.send_command_and_get_output("show running-config", router_name)
        
        # Fermer la connexion telnet
        connector.close_telnet_connection(router_name)
        
        return output
    except Exception as e:
        print(f"Erreur lors de la récupération de la configuration de {router_name}: {e}")
        return ""


def save_router_config(config: str, router_name: str, output_dir: str = "configs") -> str:
    """
    Sauvegarde la configuration d'un routeur dans un fichier.
    
    Args:
        config (str): Configuration du routeur.
        router_name (str): Nom du routeur.
        output_dir (str): Répertoire de sortie pour les fichiers de configuration.
        
    Returns:
        str: Chemin du fichier de configuration créé.
    """
    # Créer le répertoire de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Créer le chemin du fichier de sortie
    output_file = os.path.join(output_dir, f"{router_name}_config.txt")
    
    # Écrire la configuration dans le fichier
    with open(output_file, 'w') as f:
        f.write(config)
        
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
    
    for line in config.split('\n'):
        line = line.strip()
        
        # Ignorer les lignes vides et les commentaires
        if not line or line.startswith('!'):
            continue
            
        # Vérifier si c'est le début d'une nouvelle section
        interface_match = interface_pattern.match(line)
        router_match = router_pattern.match(line)
        route_map_match = route_map_pattern.match(line)
        
        if interface_match:
            current_section = f"interface_{interface_match.group(1)}"
            sections[current_section] = [line]
        elif router_match:
            protocol = router_match.group(1)
            process_id = router_match.group(2)
            current_section = f"{protocol}_{process_id}"
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


def generate_commands_from_diff(diff: Dict[str, Dict[str, List[str]]]) -> List[str]:
    """
    Génère des commandes telnet à partir d'un diff de configuration.
    
    Args:
        diff (Dict[str, Dict[str, List[str]]]): Différences entre les configurations.
        
    Returns:
        List[str]: Liste de commandes telnet à exécuter.
    """
    commands = ["enable", "configure terminal"]
    
    # Ajouter les nouvelles sections
    for section, lines in diff["added_sections"].items():
        commands.extend(lines)
    
    # Modifier les sections existantes
    for section, changes in diff["modified_sections"].items():
        # Si c'est une section d'interface
        if section.startswith("interface_"):
            interface_name = section.split("_", 1)[1]
            commands.append(f"interface {interface_name}")
            
            # Supprimer d'abord les lignes à enlever
            for line in changes.get("removed", []):
                if not line.startswith("interface"):
                    commands.append(f"no {line}")
            
            # Ajouter ensuite les nouvelles lignes
            for line in changes.get("added", []):
                if not line.startswith("interface"):
                    commands.append(line)
                    
            commands.append("exit")
        # Si c'est une section de protocole de routage
        elif section.startswith("ospf_") or section.startswith("bgp_") or section.startswith("rip_"):
            protocol, process_id = section.split("_", 1)
            commands.append(f"router {protocol} {process_id}")
            
            # Ajouter les nouvelles lignes
            for line in changes.get("added", []):
                if not line.startswith("router"):
                    commands.append(line)
                    
            commands.append("exit")
    
    commands.append("end")
    commands.append("write memory")
    
    return commands


def compare_router_configs(reference_router: str, new_router: str, connector: Connector) -> List[str]:
    """
    Compare les configurations de deux routeurs et génère les commandes pour appliquer les différences.
    
    Args:
        reference_router (str): Nom du routeur de référence.
        new_router (str): Nom du routeur avec les nouveaux protocoles.
        connector (Connector): Connecteur GNS3.
        
    Returns:
        List[str]: Liste de commandes telnet à exécuter pour appliquer les différences.
    """
    # Récupérer les configurations des routeurs
    reference_config = get_router_config(connector, reference_router)
    new_config = get_router_config(connector, new_router)
    
    # Sauvegarder les configurations
    save_router_config(reference_config, reference_router)
    save_router_config(new_config, new_router)
    
    # Parser les configurations
    parsed_reference = parse_config(reference_config)
    parsed_new = parse_config(new_config)
    
    # Comparer les configurations
    diff = compare_configs(parsed_reference, parsed_new)
    
    # Générer les commandes à partir du diff
    commands = generate_commands_from_diff(diff)
    
    return commands


def compare_networks(reference_network_file: str, new_network_file: str, output_dir: str = "diffs") -> None:
    """
    Compare deux réseaux et génère les commandes pour appliquer les différences.
    
    Args:
        reference_network_file (str): Chemin vers le fichier d'intention du réseau de référence.
        new_network_file (str): Chemin vers le fichier d'intention du réseau avec les nouveaux protocoles.
        output_dir (str): Répertoire de sortie pour les fichiers de diff.
    """
    # Créer le répertoire de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Importer les modules nécessaires ici pour éviter les imports circulaires
    from intent_parser import parse_intent_file
    from writer import get_final_config_string
    
    # Charger les réseaux
    reference_as, reference_routers = parse_intent_file(reference_network_file)
    new_as, new_routers = parse_intent_file(new_network_file)
    
    # Créer un dictionnaire des routeurs par hostname
    reference_routers_dict = {router.hostname: router for router in reference_routers}
    new_routers_dict = {router.hostname: router for router in new_routers}
    
    # Créer un dictionnaire des AS par numéro
    reference_as_dict = {as_obj.AS_number: as_obj for as_obj in reference_as}
    new_as_dict = {as_obj.AS_number: as_obj for as_obj in new_as}
    
    # Pour chaque routeur dans le nouveau réseau
    for hostname, new_router in new_routers_dict.items():
        # Vérifier si le routeur existe dans le réseau de référence
        if hostname in reference_routers_dict:
            reference_router = reference_routers_dict[hostname]
            
            # Générer les commandes telnet pour les deux routeurs
            reference_commands = get_all_telnet_commands(reference_as_dict[reference_router.AS_number], reference_router)
            new_commands = get_all_telnet_commands(new_as_dict[new_router.AS_number], new_router)
            
            # Comparer les commandes
            reference_commands_set = set(reference_commands)
            new_commands_set = set(new_commands)
            
            # Trouver les commandes ajoutées
            added_commands = new_commands_set - reference_commands_set
            
            # Écrire les commandes ajoutées dans un fichier
            output_file = os.path.join(output_dir, f"{hostname}_diff.txt")
            with open(output_file, 'w') as f:
                f.write(f"# Commandes ajoutées pour {hostname}\n")
                for cmd in sorted(added_commands):
                    f.write(f"{cmd}\n")
            
            print(f"Diff pour {hostname} écrit dans {output_file}")


def main():
    """
    Fonction principale pour exécuter la comparaison de réseaux depuis la ligne de commande.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare deux réseaux et génère les commandes pour appliquer les différences.")
    parser.add_argument("reference", help="Chemin vers le fichier d'intention du réseau de référence")
    parser.add_argument("new", help="Chemin vers le fichier d'intention du réseau avec les nouveaux protocoles")
    parser.add_argument("--output", "-o", default="diffs", help="Répertoire de sortie pour les fichiers de diff")
    
    args = parser.parse_args()
    
    compare_networks(args.reference, args.new, args.output)


if __name__ == "__main__":
    main()