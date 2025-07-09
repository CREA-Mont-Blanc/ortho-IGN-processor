"""
Configuration des seuils par défaut et profils prédéfinis
"""

# Profils de seuillage prédéfinis
DEFAULT_THRESHOLDS = {
    "foret_dense": {
        "description": "Forêt dense (couverture végétale importante)",
        "conditions": [
            {"index": "NDVI", "operator": ">", "threshold": 0.6},
            {"index": "SAVI", "operator": ">", "threshold": 0.4},
        ],
    },
    "vegetation_clairsemee": {
        "description": "Végétation clairsemée (prairies, cultures)",
        "conditions": [
            {"index": "NDVI", "operator": ">", "threshold": 0.2},
            {"index": "NDVI", "operator": "<=", "threshold": 0.6},
            {"index": "EVI", "operator": ">", "threshold": 0.1},
        ],
    },
    "zone_ombre": {
        "description": "Zones d'ombre (sous couvert forestier)",
        "conditions": [
            {"index": "SAVI", "operator": ">", "threshold": 0.3},
            {"index": "RATIO", "operator": "<", "threshold": 0.8},
            {"index": "BI_NIR", "operator": "<", "threshold": 0.4},
        ],
    },
    "zone_rocailleuse": {
        "description": "Zones rocailleuses et sol nu",
        "conditions": [
            {"index": "BSI", "operator": ">", "threshold": 0.1},
            {"index": "NDVI", "operator": "<", "threshold": 0.2},
        ],
    },
    "zone_urbaine": {
        "description": "Zones urbaines et artificialisées",
        "conditions": [
            {"index": "BI_NIR", "operator": ">", "threshold": 0.6},
            {"index": "NDVI", "operator": "<", "threshold": 0.3},
        ],
    },
    "eau": {
        "description": "Plans d'eau et zones humides",
        "conditions": [
            {"index": "RATIO", "operator": "<", "threshold": 0.3},
            {"index": "BI_NIR", "operator": "<", "threshold": 0.2},
        ],
    },
}

# Seuils recommandés par indice (pour aide à la saisie)
RECOMMENDED_RANGES = {
    "NDVI": {
        "min": -1.0,
        "max": 1.0,
        "vegetation_min": 0.2,
        "vegetation_high": 0.8,
        "water_max": 0.0,
        "soil_max": 0.2,
    },
    "SAVI": {
        "min": -1.5,
        "max": 1.5,
        "vegetation_min": 0.2,
        "vegetation_high": 0.6,
        "soil_max": 0.1,
    },
    "EVI": {"min": -1.0, "max": 1.0, "vegetation_min": 0.2, "vegetation_high": 0.8},
    "BSI": {"min": -1.0, "max": 1.0, "bare_soil_min": 0.1, "vegetation_max": -0.1},
    "RATIO": {
        "min": 0.0,
        "max": 10.0,
        "vegetation_min": 1.0,
        "water_max": 0.5,
        "soil_typical": 0.8,
    },
    "BI_NIR": {"min": 0.0, "max": 1.0, "dark_max": 0.3, "bright_min": 0.7},
    "AVI": {"min": -2.0, "max": 2.0, "vegetation_min": 0.1},
}


def get_profile_suggestions(index_name: str) -> str:
    """
    Retourne des suggestions de seuils pour un indice donné

    Args:
        index_name: Nom de l'indice

    Returns:
        Chaîne avec les suggestions
    """
    if index_name not in RECOMMENDED_RANGES:
        return "Aucune suggestion disponible"

    ranges = RECOMMENDED_RANGES[index_name]
    suggestions = []

    suggestions.append(f"Plage générale: [{ranges['min']:.1f}, {ranges['max']:.1f}]")

    if "vegetation_min" in ranges:
        suggestions.append(f"Végétation > {ranges['vegetation_min']}")

    if "vegetation_high" in ranges:
        suggestions.append(f"Végétation dense > {ranges['vegetation_high']}")

    if "soil_max" in ranges:
        suggestions.append(f"Sol nu < {ranges['soil_max']}")

    if "water_max" in ranges:
        suggestions.append(f"Eau < {ranges['water_max']}")

    if "bare_soil_min" in ranges:
        suggestions.append(f"Sol nu > {ranges['bare_soil_min']}")

    return " | ".join(suggestions)


def list_available_profiles():
    """Affiche tous les profils disponibles"""
    print("\n🎯 PROFILS PRÉDÉFINIS DISPONIBLES")
    print("=" * 40)

    for profile_name, profile_data in DEFAULT_THRESHOLDS.items():
        print(f"\n📋 {profile_name.upper().replace('_', ' ')}")
        print(f"   {profile_data['description']}")
        print("   Conditions:")
        for i, condition in enumerate(profile_data["conditions"], 1):
            print(
                f"     {i}. {condition['index']} {condition['operator']} {condition['threshold']}"
            )


def get_profile_by_name(profile_name: str) -> dict:
    """
    Récupère un profil prédéfini par son nom

    Args:
        profile_name: Nom du profil

    Returns:
        Dictionnaire du profil ou None si non trouvé
    """
    return DEFAULT_THRESHOLDS.get(profile_name.lower())


def save_custom_profile(
    name: str,
    description: str,
    conditions: list,
    config_file: str = "custom_thresholds.py",
):
    """
    Sauvegarde un profil personnalisé

    Args:
        name: Nom du profil
        description: Description du profil
        conditions: Liste des conditions
        config_file: Fichier de configuration
    """
    profile_data = {"description": description, "conditions": conditions}

    # Ajouter au fichier de configuration personnalisé
    with open(config_file, "a", encoding="utf-8") as f:
        f.write(f"\n# Profil personnalisé: {name}\n")
        f.write(f"CUSTOM_PROFILES['{name}'] = {profile_data}\n")

    print(f"✅ Profil '{name}' sauvegardé dans {config_file}")


# Dictionnaire pour les profils personnalisés (sera étendu dynamiquement)
CUSTOM_PROFILES = {}

if __name__ == "__main__":
    print("Configuration des seuils par défaut")
    list_available_profiles()

    print("\n📊 SUGGESTIONS PAR INDICE")
    print("=" * 30)
    for index_name in RECOMMENDED_RANGES.keys():
        print(f"\n{index_name}: {get_profile_suggestions(index_name)}")
