"""Module pour capturer les configurations des routeurs en mode telnet.

Ce module permet de capturer les configurations actuelles des routeurs
directement depuis GNS3 via telnet, et de les sauvegarder dans des fichiers
pour analyse ultérieure.
"""

import os
import sys
import argparse
from typing import List, Dict, Optional

from GNS3 import Connector
from parser import parse_intent_file


def capture_router_config(connector: Connector, router_name: str, output_dir: str = "configs") -> str:
    """
    Capture la configuration actuelle d'un routeur via telnet et la sauvegarde dans un fichier.
    
    Args:
        connector (Connector): Connecteur GNS3 pour communiquer avec les nœuds.
        router_name (str): Nom du routeur dont on veut capturer la configuration.
        output_dir (str): Répertoire de sortie pour les fichiers de configuration.
        
    Returns:
        str: Chemin du fichier de configuration créé.
    """
    try:
        # Établir une connexion telnet avec le routeur
        print(f"Connexion au routeur {router_name}...")
        connector.telnet_connection(router_name)
        
        # Envoyer la commande "show running-config"
        print(f"Récupération de la configuration de {router_name}...")
        output = connector.send_command_and_get_output("show running-config", router_name)
        
        # Fermer la connexion telnet
        connector.close_telnet_connection(router_name)
        
        # Créer le répertoire de sortie s'il n'existe pas
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Créer le chemin du fichier de sortie
        output_file = os.path.join(output_dir, f"{router_name}_config.txt")
        
        # Écrire la configuration dans le fichier
        with open(output_file, 'w') as f:
            f.write(output)
            
        print(f"Configuration de {router_name} sauvegardée dans {output_file}")
        return output_file
    except Exception as e:
        print(f"Erreur lors de la capture de la configuration de {router_name}: {e}")
        return ""


def capture_network_configs(intent_file: str, output_dir: str = "configs") -> Dict[str, str]:
    """
    Capture les configurations de tous les routeurs d'un réseau.
    
    Args:
        intent_file (str): Chemin vers le fichier d'intention du réseau.
        output_dir (str): Répertoire de sortie pour les fichiers de configuration.
        
    Returns:
        Dict[str, str]: Dictionnaire des chemins de fichiers de configuration par hostname.
    """
    # Charger le réseau
    _, routers = parse_intent_file(intent_file)
    
    # Créer un connecteur GNS3
    connector = Connector()
    
    # Capturer les configurations de tous les routeurs
    config_files = {}
    for router in routers:
        config_file = capture_router_config(connector, router.hostname, output_dir)
        if config_file:
            config_files[router.hostname] = config_file
    
    return config_files


def main():
    """
    Fonction principale pour exécuter la capture de configurations depuis la ligne de commande.
    """
    parser = argparse.ArgumentParser(description="Capture les configurations des routeurs en mode telnet.")
    parser.add_argument("intent_file", help="Chemin vers le fichier d'intention du réseau")
    parser.add_argument("--output", "-o", default="configs", help="Répertoire de sortie pour les fichiers de configuration")
    
    args = parser.parse_args()
    
    print(f"Capture des configurations du réseau défini dans {args.intent_file}...")
    config_files = capture_network_configs(args.intent_file, args.output)
    
    print(f"\nRésumé:")
    print(f"Nombre de configurations capturées: {len(config_files)}")
    print(f"Répertoire de sortie: {args.output}")


if __name__ == "__main__":
    main()