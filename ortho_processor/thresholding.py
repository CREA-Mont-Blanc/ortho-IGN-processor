"""
Module de seuillage pour créer des cartes thématiques
"""

import os
import numpy as np
import rasterio
from pathlib import Path
from typing import Dict, List, Tuple


class VegetationThresholder:
    """Créateur de cartes thématiques par seuillage des indices de végétation"""

    def __init__(self, output_dir: str):
        """
        Initialise le module de seuillage

        Args:
            output_dir: Répertoire de sortie pour les cartes thématiques
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def display_statistics(self, stats: Dict[str, Dict]):
        """
        Affiche les statistiques des indices de végétation

        Args:
            stats: Dictionnaire des statistiques par indice
        """
        print("\n📊 STATISTIQUES DES INDICES DE VÉGÉTATION")
        print("=" * 60)

        for index_name, index_stats in stats.items():
            print(f"\n🌿 {index_name.upper()}")
            print("-" * 30)
            print(f"  Min:         {index_stats['min']:.4f}")
            print(f"  Max:         {index_stats['max']:.4f}")
            print(f"  Moyenne:     {index_stats['mean']:.4f}")
            print(f"  Écart-type:  {index_stats['std']:.4f}")
            print(f"  Percentiles:")
            print(f"    1%:  {index_stats['percentile_1']:.4f}")
            print(f"    5%:  {index_stats['percentile_5']:.4f}")
            print(f"    25%: {index_stats['percentile_25']:.4f}")
            print(f"    75%: {index_stats['percentile_75']:.4f}")
            print(f"    95%: {index_stats['percentile_95']:.4f}")
            print(f"    99%: {index_stats['percentile_99']:.4f}")

    def get_user_thresholds(self, stats: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Demande à l'utilisateur de définir les seuils pour chaque type de zone

        Args:
            stats: Statistiques des indices

        Returns:
            Dictionnaire avec les seuils définis par l'utilisateur
        """
        print("\n🎯 DÉFINITION DES SEUILS POUR LES ZONES THÉMATIQUES")
        print("=" * 60)

        thresholds = {}

        # Zone d'ombre (végétation dense)
        print("\n🌲 ZONE D'OMBRE (Végétation dense)")
        print("Exemple suggéré: SAVI > 0.3 ET RATIO < 0.8")
        thresholds["shadow_zone"] = self._get_zone_thresholds("zone d'ombre", stats)

        # Zone rocailleuse (sol nu/rocheux)
        print("\n🪨 ZONE ROCAILLEUSE (Sol nu/rocheux)")
        print("Exemple suggéré: BSI > 0.1 ET NDVI < 0.2")
        thresholds["rocky_zone"] = self._get_zone_thresholds("zone rocailleuse", stats)

        return thresholds

    def _get_zone_thresholds(
        self, zone_name: str, stats: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Récupère les seuils pour une zone spécifique

        Args:
            zone_name: Nom de la zone
            stats: Statistiques des indices

        Returns:
            Liste des conditions de seuillage
        """
        print(f"\nDéfinition des seuils pour la {zone_name}:")
        print("Indices disponibles:", ", ".join(stats.keys()))

        conditions = []

        while True:
            print(f"\nCondition {len(conditions) + 1} pour la {zone_name}:")

            # Choix de l'indice
            while True:
                index_name = (
                    input("  Nom de l'indice (ou 'fin' pour terminer): ")
                    .strip()
                    .upper()
                )
                if index_name == "FIN":
                    return conditions
                if index_name in stats:
                    break
                print(
                    f"  ❌ Indice '{index_name}' non trouvé. Indices disponibles: {', '.join(stats.keys())}"
                )

            # Affichage des stats pour l'indice choisi
            index_stats = stats[index_name]
            print(
                f"  📊 Stats {index_name}: min={index_stats['min']:.4f}, max={index_stats['max']:.4f}, "
                f"moyenne={index_stats['mean']:.4f}"
            )

            # Choix de l'opérateur
            while True:
                operator = input("  Opérateur (>, <, >=, <=): ").strip()
                if operator in [">", "<", ">=", "<="]:
                    break
                print("  ❌ Opérateur invalide. Utilisez: >, <, >=, <=")

            # Choix de la valeur seuil
            while True:
                try:
                    threshold_value = float(input("  Valeur seuil: "))
                    break
                except ValueError:
                    print("  ❌ Veuillez entrer une valeur numérique")

            conditions.append(
                {
                    "index": index_name,
                    "operator": operator,
                    "threshold": threshold_value,
                }
            )

            print(f"  ✅ Condition ajoutée: {index_name} {operator} {threshold_value}")

            # Demander si on continue
            continue_input = (
                input("  Ajouter une autre condition? (o/n): ").strip().lower()
            )
            if continue_input not in ["o", "oui", "y", "yes"]:
                break

    def create_thematic_maps(
        self, indices_paths: Dict[str, str], thresholds: Dict[str, Dict]
    ) -> Dict[str, str]:
        """
        Crée les cartes thématiques basées sur les seuils définis

        Args:
            indices_paths: Chemins vers les fichiers d'indices
            thresholds: Seuils définis par l'utilisateur

        Returns:
            Dictionnaire avec les chemins des cartes créées
        """
        print("\n🗺️  CRÉATION DES CARTES THÉMATIQUES")
        print("=" * 50)

        thematic_maps = {}

        for zone_name, zone_conditions in thresholds.items():
            if not zone_conditions:
                continue

            print(f"\n📍 Création de la carte: {zone_name}")

            # Créer la carte pour cette zone
            map_path = self._create_zone_map(zone_name, zone_conditions, indices_paths)

            if map_path:
                thematic_maps[zone_name] = map_path
                print(f"   ✅ Carte créée: {map_path}")

        return thematic_maps

    def _create_zone_map(
        self, zone_name: str, conditions: List[Dict], indices_paths: Dict[str, str]
    ) -> str:
        """
        Crée une carte thématique pour une zone spécifique

        Args:
            zone_name: Nom de la zone
            conditions: Liste des conditions de seuillage
            indices_paths: Chemins vers les indices

        Returns:
            Chemin vers la carte créée
        """
        # Prendre le premier indice comme référence pour les métadonnées
        first_index = conditions[0]["index"]
        reference_path = indices_paths.get(first_index)

        if not reference_path or not os.path.exists(reference_path):
            print(f"   ❌ Fichier de référence non trouvé: {reference_path}")
            return None

        # Nom du fichier de sortie
        output_path = self.output_dir / f"{zone_name}_map.tif"

        with rasterio.open(reference_path) as reference:
            profile = reference.profile.copy()
            profile.update(
                {"dtype": "uint8", "count": 1, "compress": "lzw", "BIGTIFF": "YES"}
            )

            with rasterio.open(output_path, "w", **profile) as dst:
                # Traitement par blocs
                for ji, window in reference.block_windows(1):
                    # Initialiser le masque final à True (toutes les conditions satisfaites)
                    final_mask = None

                    for condition in conditions:
                        index_name = condition["index"]
                        operator = condition["operator"]
                        threshold = condition["threshold"]

                        index_path = indices_paths.get(index_name)
                        if not index_path or not os.path.exists(index_path):
                            print(f"     ⚠️  Indice {index_name} non trouvé")
                            continue

                        # Lire le bloc de l'indice
                        with rasterio.open(index_path) as src:
                            block = src.read(1, window=window)

                        # Appliquer la condition
                        if operator == ">":
                            condition_mask = block > threshold
                        elif operator == "<":
                            condition_mask = block < threshold
                        elif operator == ">=":
                            condition_mask = block >= threshold
                        elif operator == "<=":
                            condition_mask = block <= threshold
                        else:
                            continue

                        # Combiner avec les autres conditions (ET logique)
                        if final_mask is None:
                            final_mask = condition_mask
                        else:
                            final_mask = final_mask & condition_mask

                    # Créer le bloc de sortie (255 pour zone détectée, 0 sinon)
                    if final_mask is not None:
                        output_block = np.where(final_mask, 255, 0).astype(np.uint8)
                    else:
                        output_block = np.zeros(
                            (window.height, window.width), dtype=np.uint8
                        )

                    dst.write(output_block, 1, window=window)

        return str(output_path)

    def calculate_zone_statistics(
        self, thematic_maps: Dict[str, str]
    ) -> Dict[str, Dict]:
        """
        Calcule les statistiques des zones détectées

        Args:
            thematic_maps: Dictionnaire des cartes thématiques

        Returns:
            Statistiques par zone
        """
        print("\n📈 STATISTIQUES DES ZONES DÉTECTÉES")
        print("=" * 40)

        zone_stats = {}

        for zone_name, map_path in thematic_maps.items():
            if not os.path.exists(map_path):
                continue

            with rasterio.open(map_path) as src:
                data = src.read(1)
                transform = src.transform

                # Calculer les statistiques
                total_pixels = data.size
                detected_pixels = np.sum(data == 255)
                percentage = (detected_pixels / total_pixels) * 100

                # Calculer la surface (approximative)
                pixel_area = abs(transform[0] * transform[4])  # m²
                detected_area_m2 = detected_pixels * pixel_area
                detected_area_ha = detected_area_m2 / 10000  # hectares

                zone_stats[zone_name] = {
                    "total_pixels": total_pixels,
                    "detected_pixels": detected_pixels,
                    "percentage": percentage,
                    "area_m2": detected_area_m2,
                    "area_ha": detected_area_ha,
                }

                print(f"\n🗺️  {zone_name.upper().replace('_', ' ')}")
                print(f"   Pixels détectés: {detected_pixels:,} / {total_pixels:,}")
                print(f"   Pourcentage:     {percentage:.2f}%")
                print(
                    f"   Surface:         {detected_area_ha:.2f} ha ({detected_area_m2:,.0f} m²)"
                )

        return zone_stats

    def create_summary_report(
        self, zone_stats: Dict[str, Dict], thresholds: Dict[str, Dict]
    ) -> str:
        """
        Crée un rapport de synthèse

        Args:
            zone_stats: Statistiques des zones
            thresholds: Seuils utilisés

        Returns:
            Chemin vers le rapport créé
        """
        report_path = self.output_dir / "thematic_analysis_report.txt"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("RAPPORT D'ANALYSE THÉMATIQUE\n")
            f.write("=" * 50 + "\n\n")

            f.write("SEUILS UTILISÉS:\n")
            f.write("-" * 20 + "\n")
            for zone_name, conditions in thresholds.items():
                f.write(f"\n{zone_name.upper().replace('_', ' ')}:\n")
                for i, condition in enumerate(conditions, 1):
                    f.write(
                        f"  Condition {i}: {condition['index']} {condition['operator']} {condition['threshold']}\n"
                    )

            f.write("\n\nSTATISTIQUES DES ZONES:\n")
            f.write("-" * 25 + "\n")
            for zone_name, stats in zone_stats.items():
                f.write(f"\n{zone_name.upper().replace('_', ' ')}:\n")
                f.write(f"  Pixels détectés: {stats['detected_pixels']:,}\n")
                f.write(f"  Pourcentage:     {stats['percentage']:.2f}%\n")
                f.write(f"  Surface:         {stats['area_ha']:.2f} ha\n")

        print(f"\n📄 Rapport sauvegardé: {report_path}")
        return str(report_path)
