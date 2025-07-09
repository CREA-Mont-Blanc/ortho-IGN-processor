"""
Exemple d'utilisation du processeur orthophotographique en mode programmé
"""

from ortho_processor import OrthoProcessor


def example_basic_usage():
    """Exemple d'utilisation basique"""

    # Initialiser le processeur
    processor = OrthoProcessor("/path/to/working/directory")

    # Configuration manuelle (alternative au mode interactif)
    config = {
        "departments": ["74", "73"],
        "target_resolution": 2.0,
        "download_needed": False,
        "shapefile_path": "/path/to/shapefile.shp",
        "n_jobs": 4,
    }

    # Traitement étape par étape
    try:
        # 1. Vérifier les données existantes
        raw_files = processor._check_existing_data(config)

        # 2. Conversion et fusion
        ortho_files = processor._convert_and_merge(config, raw_files)

        # 3. Calcul des indices de végétation
        indices_paths = processor._calculate_vegetation_indices(config, ortho_files)

        # 4. Analyse thématique avec seuils prédéfinis
        predefined_thresholds = {
            "shadow_zone": [
                {"index": "SAVI", "operator": ">", "threshold": 0.3},
                {"index": "RATIO", "operator": "<", "threshold": 0.8},
            ],
            "rocky_zone": [
                {"index": "BSI", "operator": ">", "threshold": 0.1},
                {"index": "NDVI", "operator": "<", "threshold": 0.2},
            ],
        }

        thematic_maps = processor.thresholder.create_thematic_maps(
            indices_paths, predefined_thresholds
        )

        print("Traitement terminé!")
        print(f"Cartes créées: {list(thematic_maps.keys())}")

    except Exception as e:
        print(f"Erreur: {e}")


def example_vegetation_indices_only():
    """Exemple pour calculer uniquement les indices de végétation"""

    from ortho_processor.vegetation_indices import VegetationIndicesCalculator

    # Fichiers d'entrée (RGBNIR)
    input_files = ["/path/to/ortho1.tif", "/path/to/ortho2.tif"]

    # Shapefile de découpage (optionnel)
    shapefile_path = "/path/to/boundary.shp"

    # Calculateur d'indices
    calculator = VegetationIndicesCalculator("/path/to/output")

    # Calcul des indices
    indices_paths = calculator.process_files(input_files, shapefile_path)

    # Statistiques
    stats = calculator.get_indices_statistics(indices_paths)

    print("Indices calculés:")
    for index_name, path in indices_paths.items():
        print(f"  {index_name}: {path}")


def example_thematic_mapping_only():
    """Exemple pour créer uniquement des cartes thématiques"""

    from ortho_processor.thresholding import VegetationThresholder

    # Chemins vers les indices existants
    indices_paths = {
        "NDVI": "/path/to/NDVI.tif",
        "SAVI": "/path/to/SAVI.tif",
        "BSI": "/path/to/BSI.tif",
        "RATIO": "/path/to/RATIO.tif",
    }

    # Seuils prédéfinis
    thresholds = {
        "vegetation_dense": [
            {"index": "NDVI", "operator": ">", "threshold": 0.5},
            {"index": "SAVI", "operator": ">", "threshold": 0.4},
        ],
        "sol_nu": [
            {"index": "BSI", "operator": ">", "threshold": 0.2},
            {"index": "NDVI", "operator": "<", "threshold": 0.1},
        ],
    }

    # Créateur de cartes thématiques
    thresholder = VegetationThresholder("/path/to/thematic_output")

    # Créer les cartes
    thematic_maps = thresholder.create_thematic_maps(indices_paths, thresholds)

    # Calculer les statistiques
    zone_stats = thresholder.calculate_zone_statistics(thematic_maps)

    # Rapport
    report_path = thresholder.create_summary_report(zone_stats, thresholds)

    print(f"Cartes créées: {list(thematic_maps.keys())}")
    print(f"Rapport: {report_path}")


if __name__ == "__main__":
    print("Exemples d'utilisation du processeur orthophotographique")
    print("=" * 60)

    # Décommenter l'exemple souhaité
    # example_basic_usage()
    # example_vegetation_indices_only()
    # example_thematic_mapping_only()

    print("Modifiez le script pour exécuter l'exemple souhaité")
