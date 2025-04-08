#!/usr/bin/env python3
"""
Script principal pour comparer les fichiers de configuration des routeurs.

Ce script permet de comparer deux fichiers de configuration de routeurs (.cfg) et de générer
un rapport détaillé des différences, facilitant ainsi l'analyse des changements entre deux configurations.
"""

import os
import sys
import argparse
from typing import Dict, List, Optional

from GNS3 import Connector
from capture_config import capture_router_config
from compare_router_configs import compare_router_config_files, compare_running_configs
from config_diff_report import generate_config_diff_report
import os


def file_exists(filepath: str) -> bool:
    """Vérifie si un fichier existe."""
    return os.path.isfile(filepath)


def main():
    """
    Fonction principale pour exécuter la comparaison de fichiers de configuration depuis la ligne de commande.
    """
    parser = argparse.ArgumentParser(
        description="Compare les fichiers de configuration des routeurs et génère un rapport des différences."
    )
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Sous-commande pour comparer deux fichiers de configuration
    file_parser = subparsers.add_parser("files", help="Compare deux fichiers de configuration")
    file_parser.add_argument("reference", help="Chemin vers le fichier de configuration du routeur de référence")
    file_parser.add_argument("new", help="Chemin vers le fichier de configuration du routeur avec les nouveaux protocoles")
    file_parser.add_argument("--output", "-o", default="diffs", help="Répertoire de sortie pour les fichiers de diff")
    file_parser.add_argument("--format", "-f", choices=["text", "html"], default="text", 
                            help="Format du rapport de différences (text ou html)")
    
    # Sous-commande pour comparer deux routeurs en cours d'exécution
    running_parser = subparsers.add_parser("running", help="Compare deux routeurs en cours d'exécution")
    running_parser.add_argument("reference", help="Nom du routeur de référence")
    running_parser.add_argument("new", help="Nom du routeur avec les nouveaux protocoles")
    running_parser.add_argument("--output", "-o", default="diffs", help="Répertoire de sortie pour les fichiers de diff")
    running_parser.add_argument("--format", "-f", choices=["text", "html"], default="text", 
                               help="Format du rapport de différences (text ou html)")
    
    # Sous-commande pour capturer la configuration d'un routeur
    capture_parser = subparsers.add_parser("capture", help="Capture la configuration d'un routeur")
    capture_parser.add_argument("router", help="Nom du routeur à capturer")
    capture_parser.add_argument("--output", "-o", default="configs", help="Répertoire de sortie pour les fichiers de configuration")
    
    args = parser.parse_args()
    
    if args.command == "files":
        print(f"Comparaison des configurations {args.reference} et {args.new}...")
        
        if not file_exists(args.reference):
            print(f"Erreur : Le fichier de référence '{args.reference}' est introuvable.")
            sys.exit(1)
        if not file_exists(args.new):
            print(f"Erreur : Le fichier '{args.new}' est introuvable.")
            sys.exit(1)

        if args.format == "html":
            # Extraction des noms de fichiers pour plus de clarté dans les rapports
            ref_name = os.path.basename(args.reference).split('.')[0]
            new_name = os.path.basename(args.new).split('.')[0]
            # Modifier l'appel pour utiliser uniquement les arguments acceptés
            output_file = generate_config_diff_report(args.reference, args.new, args.output)
        else:
            diff = compare_router_config_files(args.reference, args.new, args.output)
            print("\nRésumé des différences:")
            print(f"Sections ajoutées: {len(diff['added_sections'])}")
            print(f"Sections supprimées: {len(diff['removed_sections'])}")
            print(f"Sections modifiées: {len(diff['modified_sections'])}")
    
    elif args.command == "running":
        print(f"Comparaison des configurations en cours d'exécution de {args.reference} et {args.new}...")
        connector = Connector()
        
        try:
            # Capturer les configurations
            reference_config_file = capture_router_config(connector, args.reference, "configs")
            new_config_file = capture_router_config(connector, args.new, "configs")
        except AttributeError as e:
            print(f"Erreur : {e}. Vérifiez que la classe Connector possède la méthode 'send_command_and_get_output'.")
            sys.exit(1)

        if not file_exists(reference_config_file) or not file_exists(new_config_file):
            print("Erreur : L'un des fichiers de configuration capturés est introuvable.")
            sys.exit(1)
        
        if args.format == "html":
            # Modifier l'appel pour utiliser uniquement les arguments acceptés
            output_file = generate_config_diff_report(reference_config_file, new_config_file, args.output)
        else:
            diff = compare_router_config_files(reference_config_file, new_config_file, args.output)
            print("\nRésumé des différences:")
            print(f"Sections ajoutées: {len(diff['added_sections'])}")
            print(f"Sections supprimées: {len(diff['removed_sections'])}")
            print(f"Sections modifiées: {len(diff['modified_sections'])}")
    
    elif args.command == "capture":
        print(f"Capture de la configuration du routeur {args.router}...")
        connector = Connector()
        try:
            config_file = capture_router_config(connector, args.router, args.output)
        except AttributeError as e:
            print(f"Erreur : {e}. Vérifiez que la classe Connector possède la méthode 'send_command_and_get_output'.")
            sys.exit(1)

        if config_file and file_exists(config_file):
            print(f"Configuration capturée avec succès dans {config_file}")
        else:
            print("Erreur : Échec de la capture de la configuration.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
