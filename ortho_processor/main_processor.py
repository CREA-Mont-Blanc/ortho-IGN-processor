"""
Module principal du processeur orthophotographique interactif
"""

import os
from pathlib import Path
from typing import List, Dict, Optional

from .downloader import OrthoDownloader
from .converter import OrthoConverter
from .vegetation_indices import VegetationIndicesCalculator
from .thresholding import VegetationThresholder


class OrthoProcessor:
    """Processeur principal interactif pour les données orthophotographiques"""

    def __init__(self, base_dir: str):
        """
        Initialise le processeur principal

        Args:
            base_dir: Répertoire de base pour tous les traitements
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Initialiser les modules
        self.downloader = OrthoDownloader(str(self.base_dir / "raw_data"))
        self.converter = OrthoConverter(
            str(self.base_dir / "raw_data"), str(self.base_dir / "processed")
        )
        self.vegetation_calculator = VegetationIndicesCalculator(
            str(self.base_dir / "vegetation_indices")
        )
        self.thresholder = VegetationThresholder(str(self.base_dir / "thematic_maps"))

    def run_interactive_workflow(self):
        """
        Lance le workflow interactif complet
        """
        print("🚀 PROCESSEUR ORTHOPHOTOGRAPHIQUE INTERACTIF")
        print("=" * 50)

        try:
            # Étape 1: Configuration
            config = self._get_user_configuration()

            # Étape 2: Téléchargement/Vérification des données
            if config["download_needed"]:
                raw_files = self._download_data(config)
            else:
                raw_files = self._check_existing_data(config)

            # Étape 3: Conversion et fusion
            final_ortho = self._convert_and_merge(config, raw_files)

            # Étape 4: Calcul des indices de végétation
            indices_paths = self._calculate_vegetation_indices(config, final_ortho)

            # Étape 5: Analyse thématique
            self._perform_thematic_analysis(indices_paths)

            print("\n🎉 TRAITEMENT TERMINÉ AVEC SUCCÈS!")

        except KeyboardInterrupt:
            print("\n⏹️  Traitement interrompu par l'utilisateur")
        except Exception as e:
            print(f"\n❌ Erreur: {e}")

    def _get_user_configuration(self) -> Dict:
        """
        Récupère la configuration utilisateur

        Returns:
            Dictionnaire de configuration
        """
        print("\n📋 CONFIGURATION")
        print("-" * 20)

        config = {}

        # Départements à traiter
        departments_input = input("Départements à traiter (ex: 74,73,38): ").strip()
        config["departments"] = [
            d.strip() for d in departments_input.split(",") if d.strip()
        ]

        if not config["departments"]:
            raise ValueError("Au moins un département doit être spécifié")

        # Résolution cible
        while True:
            try:
                resolution_input = input(
                    "Résolution cible en mètres (ex: 2.0): "
                ).strip()
                config["target_resolution"] = float(resolution_input)
                break
            except ValueError:
                print("❌ Veuillez entrer une valeur numérique valide")

        # Téléchargement nécessaire
        download_input = input("Télécharger les données? (o/n): ").strip().lower()
        config["download_needed"] = download_input in ["o", "oui", "y", "yes"]

        # Fichier d'URLs (si téléchargement nécessaire)
        if config["download_needed"]:
            urls_file_input = input("Fichier contenant les URLs (optionnel): ").strip()
            config["urls_file"] = urls_file_input if urls_file_input else None
        else:
            config["urls_file"] = None

        # Shapefile de découpage (optionnel)
        shapefile_input = input(
            "Chemin vers shapefile de découpage (optionnel): "
        ).strip()
        config["shapefile_path"] = shapefile_input if shapefile_input else None

        # Nombre de processus parallèles
        while True:
            try:
                n_jobs_input = input(
                    "Nombre de processus parallèles (défaut: 4): "
                ).strip()
                config["n_jobs"] = int(n_jobs_input) if n_jobs_input else 4
                break
            except ValueError:
                print("❌ Veuillez entrer un nombre entier")

        return config

    def _download_data(self, config: Dict) -> Dict[str, Dict[str, List[str]]]:
        """
        Télécharge les données pour tous les départements

        Args:
            config: Configuration utilisateur

        Returns:
            Dictionnaire des fichiers téléchargés par département
        """
        print("\n📥 TÉLÉCHARGEMENT DES DONNÉES")
        print("-" * 30)

        raw_files = {}

        for department in config["departments"]:
            print(f"\n📂 Département {department}")
            files_by_band = self.downloader.download_department_data(
                department, bands=["IRC", "RVB"], urls_file=config["urls_file"]
            )
            raw_files[department] = files_by_band

            # Afficher les statistiques
            stats = self.downloader.get_stats(department)
            self._display_download_stats(stats)

        return raw_files

    def _check_existing_data(self, config: Dict) -> Dict[str, Dict[str, List[str]]]:
        """
        Vérifie les données existantes

        Args:
            config: Configuration utilisateur

        Returns:
            Dictionnaire des fichiers existants par département
        """
        print("\n📂 VÉRIFICATION DES DONNÉES EXISTANTES")
        print("-" * 40)

        raw_files = {}

        for department in config["departments"]:
            files_by_band = self.downloader.list_available_files(department)

            if not files_by_band:
                raise ValueError(
                    f"Aucune donnée trouvée pour le département {department}"
                )

            raw_files[department] = files_by_band

            # Afficher les statistiques
            stats = self.downloader.get_stats(department)
            self._display_download_stats(stats)

        return raw_files

    def _convert_and_merge(self, config: Dict, raw_files: Dict) -> List[str]:
        """
        Convertit et fusionne les données

        Args:
            config: Configuration utilisateur
            raw_files: Fichiers bruts par département

        Returns:
            Liste des fichiers orthophotographiques finaux
        """
        print("\n🔄 CONVERSION ET FUSION")
        print("-" * 25)

        final_orthos = []

        for department in config["departments"]:
            print(f"\n🏗️  Traitement du département {department}")

            # Conversion JP2 -> TIFF
            converted_files = self.converter.convert_department_files(
                department, config["target_resolution"], config["n_jobs"]
            )

            # Fusion des bandes
            if "IRC" in converted_files and "RVB" in converted_files:
                merged_files = self.converter.merge_bands(
                    converted_files["IRC"],
                    converted_files["RVB"],
                    config["target_resolution"],
                    config["n_jobs"],
                )

                # Création de la mosaïque finale
                final_ortho = self.converter.create_final_mosaic(
                    merged_files, department, config["target_resolution"]
                )

                final_orthos.append(final_ortho)
            else:
                print(
                    f"   ⚠️  Bandes IRC ou RVB manquantes pour le département {department}"
                )

        return final_orthos

    def _calculate_vegetation_indices(
        self, config: Dict, ortho_files: List[str]
    ) -> Dict[str, str]:
        """
        Calcule les indices de végétation

        Args:
            config: Configuration utilisateur
            ortho_files: Fichiers orthophotographiques finaux

        Returns:
            Chemins vers les indices calculés
        """
        print("\n🌱 CALCUL DES INDICES DE VÉGÉTATION")
        print("-" * 35)

        # Filtrer les fichiers existants
        existing_files = [f for f in ortho_files if os.path.exists(f)]

        if not existing_files:
            raise ValueError("Aucun fichier orthophotographique trouvé")

        # Calculer les indices
        indices_paths = self.vegetation_calculator.process_files(
            existing_files, config["shapefile_path"]
        )

        return indices_paths

    def _perform_thematic_analysis(self, indices_paths: Dict[str, str]):
        """
        Effectue l'analyse thématique interactive

        Args:
            indices_paths: Chemins vers les indices de végétation
        """
        print("\n🗺️  ANALYSE THÉMATIQUE")
        print("-" * 20)

        # Calculer les statistiques des indices
        stats = self.vegetation_calculator.get_indices_statistics(indices_paths)

        # Afficher les statistiques
        self.thresholder.display_statistics(stats)

        # Demander les seuils à l'utilisateur
        thresholds = self.thresholder.get_user_thresholds(stats)

        # Créer les cartes thématiques
        thematic_maps = self.thresholder.create_thematic_maps(indices_paths, thresholds)

        # Calculer les statistiques des zones
        zone_stats = self.thresholder.calculate_zone_statistics(thematic_maps)

        # Créer le rapport de synthèse
        report_path = self.thresholder.create_summary_report(zone_stats, thresholds)

        print(f"\n📊 Analyse terminée. Rapport disponible: {report_path}")

    def _display_download_stats(self, stats: Dict):
        """
        Affiche les statistiques de téléchargement

        Args:
            stats: Statistiques des fichiers
        """
        print(f"   📊 Total: {stats['total_files']} fichiers")
        for band, band_stats in stats["bands"].items():
            print(
                f"   📁 {band}: {band_stats['file_count']} fichiers "
                f"({band_stats['total_size_gb']:.2f} Go)"
            )


def main():
    """Point d'entrée principal"""
    print("🌍 PROCESSEUR ORTHOPHOTOGRAPHIQUE")
    print("Analyseur de végétation et cartographie thématique")
    print("=" * 50)

    # Demander le répertoire de travail
    while True:
        base_dir = input("\nRépertoire de travail: ").strip()
        if base_dir:
            try:
                Path(base_dir).mkdir(parents=True, exist_ok=True)
                break
            except Exception as e:
                print(f"❌ Erreur avec le répertoire: {e}")
        else:
            print("❌ Veuillez spécifier un répertoire")

    # Lancer le processeur
    processor = OrthoProcessor(base_dir)
    processor.run_interactive_workflow()


if __name__ == "__main__":
    main()
