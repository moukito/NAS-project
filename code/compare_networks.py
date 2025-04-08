"""Module principal pour comparer deux réseaux et générer les commandes d'implémentation.

Ce module permet de comparer un réseau de référence avec un réseau contenant des
protocoles supplémentaires, et de générer les commandes telnet nécessaires pour
implémenter ces différences.
"""

import os
import sys
import argparse
from typing import List, Dict, Tuple, Set

from GNS3 import Connector
from intent_parser import parse_intent_file
from writer import get_all_telnet_commands
from capture_config import capture_router_config
from config_diff import compare_configs, parse_config, generate_commands_from_diff


def generate_diff_from_intent_files(reference_file: str, new_file: str, output_dir: str = "diffs") -> Dict[str, List[str]]:
    """
    Génère les différences entre deux réseaux à partir des fichiers d'intention.
    
    Args:
        reference_file (str): Chemin vers le fichier d'intention du réseau de référence.
        new_file (str): Chemin vers le fichier d'intention du réseau avec les nouveaux protocoles.
        output_dir (str): Répertoire de sortie pour les fichiers de diff.
        
    Returns:
        Dict[str, List[str]]: Dictionnaire des commandes à exécuter par hostname.
    """
    # Créer le répertoire de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Charger les réseaux
    reference_as, reference_routers = parse_intent_file(reference_file)
    new_as, new_routers = parse_intent_file(new_file)
    
    # Créer un dictionnaire des routeurs par hostname
    reference_routers_dict = {router.hostname: router for router in reference_routers}
    new_routers_dict = {router.hostname: router for router in new_routers}
    
    # Créer un dictionnaire des AS par numéro
    reference_as_dict = {as_obj.AS_number: as_obj for as_obj in reference_as}
    new_as_dict = {as_obj.AS_number: as_obj for as_obj in new_as}
    
    # Dictionnaire pour stocker les commandes par hostname
    commands_by_hostname = {}
    
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
            added_commands = list(new_commands_set - reference_commands_set)
            
            # Si des commandes ont été ajoutées, les enregistrer
            if added_commands:
                commands_by_hostname[hostname] = added_commands
                
                # Écrire les commandes ajoutées dans un fichier
                output_file = os.path.join(output_dir, f"{hostname}_diff.txt")
                with open(output_file, 'w') as f:
                    f.write(f"# Commandes ajoutées pour {hostname}\n")
                    for cmd in sorted(added_commands):
                        f.write(f"{cmd}\n")
                
                print(f"Diff pour {hostname} écrit dans {output_file}")
    
    return commands_by_hostname


def generate_diff_from_running_configs(reference_router: str, new_router: str, connector: Connector, output_dir: str = "diffs") -> List[str]:
    """
    Génère les différences entre deux routeurs à partir de leurs configurations en cours d'exécution.
    
    Args:
        reference_router (str): Nom du routeur de référence.
        new_router (str): Nom du routeur avec les nouveaux protocoles.
        connector (Connector): Connecteur GNS3.
        output_dir (str): Répertoire de sortie pour les fichiers de diff.
        
    Returns:
        List[str]: Liste de commandes telnet à exécuter pour appliquer les différences.
    """
    # Créer le répertoire de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Capturer les configurations des routeurs
    reference_config_file = capture_router_config(connector, reference_router, "configs")
    new_config_file = capture_router_config(connector, new_router, "configs")
    
    # Lire les configurations
    with open(reference_config_file, 'r') as f:
        reference_config = f.read()
    
    with open(new_config_file, 'r') as f:
        new_config = f.read()
    
    # Parser les configurations
    parsed_reference = parse_config(reference_config)
    parsed_new = parse_config(new_config)
    
    # Comparer les configurations
    diff = compare_configs(parsed_reference, parsed_new)
    
    # Générer les commandes à partir du diff
    commands = generate_commands_from_diff(diff)
    
    # Écrire les commandes dans un fichier
    output_file = os.path.join(output_dir, f"{reference_router}_to_{new_router}_diff.txt")
    with open(output_file, 'w') as f:
        f.write(f"# Commandes pour transformer {reference_router} en {new_router}\n")
        for cmd in commands:
            f.write(f"{cmd}\n")
    
    print(f"Diff écrit dans {output_file}")
    
    return commands


def apply_diff_to_router(router_name: str, commands: List[str], connector: Connector) -> bool:
    """
    Applique les commandes de différence à un routeur.
    
    Args:
        router_name (str): Nom du routeur.
        commands (List[str]): Liste de commandes à exécuter.
        connector (Connector): Connecteur GNS3.
        
    Returns:
        bool: True si l'application a réussi, False sinon.
    """
    try:
        # Établir une connexion telnet avec le routeur
        print(f"Connexion au routeur {router_name}...")
        connector.telnet_connection(router_name)
        
        # Envoyer les commandes
        print(f"Application des commandes à {router_name}...")
        connector.send_commands_to_node(commands, router_name)
        
        # Fermer la connexion telnet
        connector.close_telnet_connection(router_name)
        
        print(f"Commandes appliquées avec succès à {router_name}")
        return True
    except Exception as e:
        print(f"Erreur lors de l'application des commandes à {router_name}: {e}")
        return False


def main():
    """
    Fonction principale pour exécuter la comparaison de réseaux depuis la ligne de commande.
    """
    parser = argparse.ArgumentParser(description="Compare deux réseaux et génère les commandes pour appliquer les différences.")
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Sous-commande pour comparer deux fichiers d'intention
    intent_parser = subparsers.add_parser("intent", help="Compare deux fichiers d'intention")
    intent_parser.add_argument("reference", help="Chemin vers le fichier d'intention du réseau de référence")
    intent_parser.add_argument("new", help="Chemin vers le fichier d'intention du réseau avec les nouveaux protocoles")
    intent_parser.add_argument("--output", "-o", default="diffs", help="Répertoire de sortie pour les fichiers de diff")
    intent_parser.add_argument("--apply", "-a", action="store_true", help="Appliquer les différences aux routeurs")
    
    # Sous-commande pour comparer deux routeurs en cours d'exécution
    running_parser = subparsers.add_parser("running", help="Compare deux routeurs en cours d'exécution")
    running_parser.add_argument("reference", help="Nom du routeur de référence")
    running_parser.add_argument("new", help="Nom du routeur avec les nouveaux protocoles")
    running_parser.add_argument("--output", "-o", default="diffs", help="Répertoire de sortie pour les fichiers de diff")
    running_parser.add_argument("--apply", "-a", help="Nom du routeur auquel appliquer les différences")
    
    args = parser.parse_args()
    
    # Créer un connecteur GNS3
    connector = Connector()
    
    if args.command == "intent":
        print(f"Comparaison des réseaux définis dans {args.reference} et {args.new}...")
        commands_by_hostname = generate_diff_from_intent_files(args.reference, args.new, args.output)
        
        if args.apply:
            print("\nApplication des différences aux routeurs...")
            for hostname, commands in commands_by_hostname.items():
                apply_diff_to_router(hostname, commands, connector)
    
    elif args.command == "running":
        print(f"Comparaison des routeurs {args.reference} et {args.new}...")
        commands = generate_diff_from_running_configs(args.reference, args.new, connector, args.output)
        
        if args.apply:
            print(f"\nApplication des différences au routeur {args.apply}...")
            apply_diff_to_router(args.apply, commands, connector)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()