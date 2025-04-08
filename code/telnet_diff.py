"""Module pour comparer deux configurations telnet et générer un diff.

Ce module permet de comparer deux configurations telnet de routeurs similaires
afin d'identifier les différences et faciliter l'implémentation de nouveaux protocoles.
"""

import os
import sys
import argparse
from typing import List, Dict, Set, Tuple

from GNS3 import Connector
from writer import get_all_telnet_commands
from intent_parser import parse_intent_file, router_list_into_hostname_dictionary, as_list_into_as_number_dictionary


def extract_commands_from_file(file_path: str) -> List[str]:
    """
    Extrait les commandes telnet d'un fichier.
    
    Args:
        file_path (str): Chemin vers le fichier contenant les commandes.
        
    Returns:
        List[str]: Liste des commandes telnet.
    """
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


def save_commands_to_file(commands: List[str], output_file: str) -> None:
    """
    Sauvegarde les commandes telnet dans un fichier.
    
    Args:
        commands (List[str]): Liste des commandes telnet.
        output_file (str): Chemin du fichier de sortie.
    """
    with open(output_file, 'w') as f:
        for cmd in commands:
            f.write(f"{cmd}\n")


def compare_commands(reference_commands: List[str], new_commands: List[str]) -> Tuple[List[str], List[str]]:
    """
    Compare deux listes de commandes telnet et identifie les différences.
    
    Args:
        reference_commands (List[str]): Commandes du routeur de référence.
        new_commands (List[str]): Commandes du routeur avec les nouveaux protocoles.
        
    Returns:
        Tuple[List[str], List[str]]: Tuple contenant les commandes ajoutées et supprimées.
    """
    reference_set = set(reference_commands)
    new_set = set(new_commands)
    
    added = list(new_set - reference_set)
    removed = list(reference_set - new_set)
    
    return added, removed


def generate_diff_from_intent_files(reference_file: str, new_file: str, output_dir: str = "diffs") -> Dict[str, Dict[str, List[str]]]:
    """
    Génère les différences entre deux réseaux à partir des fichiers d'intention.
    
    Args:
        reference_file (str): Chemin vers le fichier d'intention du réseau de référence.
        new_file (str): Chemin vers le fichier d'intention du réseau avec les nouveaux protocoles.
        output_dir (str): Répertoire de sortie pour les fichiers de diff.
        
    Returns:
        Dict[str, Dict[str, List[str]]]: Dictionnaire des commandes ajoutées et supprimées par hostname.
    """
    # Créer le répertoire de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Charger les réseaux
    reference_as, reference_routers = parse_intent_file(reference_file)
    new_as, new_routers = parse_intent_file(new_file)
    
    # Créer un dictionnaire des routeurs par hostname
    reference_routers_dict = router_list_into_hostname_dictionary(reference_routers)
    new_routers_dict = router_list_into_hostname_dictionary(new_routers)
    
    # Créer un dictionnaire des AS par numéro
    reference_as_dict = as_list_into_as_number_dictionary(reference_as)
    new_as_dict = as_list_into_as_number_dictionary(new_as)
    
    # Dictionnaire pour stocker les commandes par hostname
    diff_by_hostname = {}
    
    # Pour chaque routeur dans le nouveau réseau
    for hostname, new_router in new_routers_dict.items():
        # Vérifier si le routeur existe dans le réseau de référence
        if hostname in reference_routers_dict:
            reference_router = reference_routers_dict[hostname]
            
            # Générer les commandes telnet pour les deux routeurs
            reference_commands = get_all_telnet_commands(reference_as_dict[reference_router.AS_number], reference_router)
            new_commands = get_all_telnet_commands(new_as_dict[new_router.AS_number], new_router)
            
            # Comparer les commandes
            added, removed = compare_commands(reference_commands, new_commands)
            
            # Si des différences ont été trouvées, les enregistrer
            if added or removed:
                diff_by_hostname[hostname] = {
                    "added": added,
                    "removed": removed
                }
                
                # Écrire les commandes ajoutées dans un fichier
                if added:
                    added_file = os.path.join(output_dir, f"{hostname}_added.txt")
                    save_commands_to_file(added, added_file)
                    print(f"Commandes ajoutées pour {hostname} écrites dans {added_file}")
                
                # Écrire les commandes supprimées dans un fichier
                if removed:
                    removed_file = os.path.join(output_dir, f"{hostname}_removed.txt")
                    save_commands_to_file(removed, removed_file)
                    print(f"Commandes supprimées pour {hostname} écrites dans {removed_file}")
                
                # Écrire un fichier de commandes d'implémentation
                if added:
                    impl_file = os.path.join(output_dir, f"{hostname}_implementation.txt")
                    # Filtrer les commandes de base qui sont toujours présentes
                    implementation_commands = [cmd for cmd in added if cmd not in ["enable", "configure terminal", "end", "write memory"]]
                    
                    # Ajouter les commandes de début et de fin
                    if implementation_commands:
                        full_implementation = ["enable", "configure terminal"] + implementation_commands + ["end", "write memory"]
                        save_commands_to_file(full_implementation, impl_file)
                        print(f"Commandes d'implémentation pour {hostname} écrites dans {impl_file}")
    
    return diff_by_hostname


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
    parser.add_argument("reference", help="Chemin vers le fichier d'intention du réseau de référence")
    parser.add_argument("new", help="Chemin vers le fichier d'intention du réseau avec les nouveaux protocoles")
    parser.add_argument("--output", "-o", default="diffs", help="Répertoire de sortie pour les fichiers de diff")
    parser.add_argument("--apply", "-a", action="store_true", help="Appliquer les différences aux routeurs")
    parser.add_argument("--router", "-r", help="Nom du routeur spécifique à traiter (optionnel)")
    
    args = parser.parse_args()
    
    print(f"Comparaison des réseaux définis dans {args.reference} et {args.new}...")
    diff_by_hostname = generate_diff_from_intent_files(args.reference, args.new, args.output)
    
    if args.apply:
        # Créer un connecteur GNS3
        connector = Connector()
        
        print("\nApplication des différences aux routeurs...")
        for hostname, diff in diff_by_hostname.items():
            # Si un routeur spécifique est demandé, ne traiter que celui-là
            if args.router and args.router != hostname:
                continue
                
            if diff["added"]:
                # Filtrer les commandes de base qui sont toujours présentes
                implementation_commands = [cmd for cmd in diff["added"] if cmd not in ["enable", "configure terminal", "end", "write memory"]]
                
                # Ajouter les commandes de début et de fin
                if implementation_commands:
                    full_implementation = ["enable", "configure terminal"] + implementation_commands + ["end", "write memory"]
                    apply_diff_to_router(hostname, full_implementation, connector)


if __name__ == "__main__":
    main()