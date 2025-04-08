"""Module pour générer un rapport HTML des différences entre deux configurations de routeurs.

Ce module permet de comparer deux fichiers de configuration de routeurs (.cfg) et de générer
un rapport HTML détaillé des différences, facilitant ainsi l'analyse visuelle des changements.
"""

import os
import re
import argparse
from typing import Dict, List, Tuple, Set, Optional
from datetime import datetime

from compare_router_configs import load_config_file, parse_config, compare_configs, extract_hostname


def generate_html_diff(diff: Dict[str, Dict[str, List[str]]], reference_name: str, new_name: str, output_dir: str = "diffs") -> str:
    """
    Génère un rapport HTML des différences entre deux configurations de routeurs.
    
    Args:
        diff (Dict[str, Dict[str, List[str]]]): Différences entre les configurations.
        reference_name (str): Nom du routeur de référence.
        new_name (str): Nom du routeur avec les nouveaux protocoles.
        output_dir (str): Répertoire de sortie pour les fichiers de diff.
        
    Returns:
        str: Chemin du fichier HTML généré.
    """
    # Créer le répertoire de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Créer le chemin du fichier de sortie
    output_file = os.path.join(output_dir, f"{reference_name}_to_{new_name}_diff.html")
    
    # Date et heure actuelles
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Générer le contenu HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Différences de configuration entre {reference_name} et {new_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #2980b9; margin-top: 30px; }}
            h3 {{ color: #3498db; margin-top: 20px; }}
            h4 {{ color: #16a085; margin-top: 15px; }}
            pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            .added {{ background-color: #e6ffed; }}
            .removed {{ background-color: #ffeef0; }}
            .modified {{ background-color: #fff5b1; }}
            .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .timestamp {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 20px; }}
            .section-count {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Différences de configuration entre {reference_name} et {new_name}</h1>
        <div class="timestamp">Généré le {now}</div>
        
        <div class="summary">
            <h2>Résumé des différences</h2>
            <p><span class="section-count">{len(diff['added_sections'])}</span> sections ajoutées</p>
            <p><span class="section-count">{len(diff['removed_sections'])}</span> sections supprimées</p>
            <p><span class="section-count">{len(diff['modified_sections'])}</span> sections modifiées</p>
        </div>
    """
    
    # Sections ajoutées
    if diff["added_sections"]:
        html_content += """
        <h2 class="added">Sections ajoutées</h2>
        """
        for section, lines in sorted(diff["added_sections"].items()):
            html_content += f"""
            <h3>{section}</h3>
            <pre class="added">
"""
            for line in lines:
                html_content += f"{line}\n"
            html_content += "</pre>\n"
    
    # Sections supprimées
    if diff["removed_sections"]:
        html_content += """
        <h2 class="removed">Sections supprimées</h2>
        """
        for section, lines in sorted(diff["removed_sections"].items()):
            html_content += f"""
            <h3>{section}</h3>
            <pre class="removed">
"""
            for line in lines:
                html_content += f"{line}\n"
            html_content += "</pre>\n"
    
    # Sections modifiées
    if diff["modified_sections"]:
        html_content += """
        <h2 class="modified">Sections modifiées</h2>
        """
        for section, changes in sorted(diff["modified_sections"].items()):
            html_content += f"""
            <h3>{section}</h3>
            """
            
            # Lignes ajoutées
            if changes.get("added"):
                html_content += """
                <h4>Lignes ajoutées</h4>
                <pre class="added">
                """
                for line in sorted(changes["added"]):
                    html_content += f"{line}\n"
                html_content += "</pre>\n"
            
            # Lignes supprimées
            if changes.get("removed"):
                html_content += """
                <h4>Lignes supprimées</h4>
                <pre class="removed">
                """
                for line in sorted(changes["removed"]):
                    html_content += f"{line}\n"
                html_content += "</pre>\n"
    
    # Fermer le document HTML
    html_content += """
    </body>
    </html>
    """
    
    # Écrire le contenu HTML dans le fichier
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Rapport HTML écrit dans {output_file}")
    return output_file


def generate_config_diff_report(reference_config_file: str, new_config_file: str, output_dir: str = "diffs") -> str:
    """
    Génère un rapport HTML des différences entre deux fichiers de configuration de routeurs.
    
    Args:
        reference_config_file (str): Chemin vers le fichier de configuration du routeur de référence.
        new_config_file (str): Chemin vers le fichier de configuration du routeur avec les nouveaux protocoles.
        output_dir (str): Répertoire de sortie pour les fichiers de diff.
        
    Returns:
        str: Chemin du fichier HTML généré.
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
    
    # Générer le rapport HTML
    return generate_html_diff(diff, reference_name, new_name, output_dir)


def main():
    """
    Fonction principale pour exécuter la génération de rapport depuis la ligne de commande.
    """
    parser = argparse.ArgumentParser(description="Génère un rapport HTML des différences entre deux fichiers de configuration de routeurs.")
    parser.add_argument("reference", help="Chemin vers le fichier de configuration du routeur de référence")
    parser.add_argument("new", help="Chemin vers le fichier de configuration du routeur avec les nouveaux protocoles")
    parser.add_argument("--output", "-o", default="diffs", help="Répertoire de sortie pour les fichiers de diff")
    
    args = parser.parse_args()
    
    print(f"Génération du rapport de différences entre {args.reference} et {args.new}...")
    output_file = generate_config_diff_report(args.reference, args.new, args.output)
    print(f"Rapport généré avec succès dans {output_file}")


if __name__ == "__main__":
    main()