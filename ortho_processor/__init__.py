"""
Package de traitement des données orthophotographiques et calcul d'indices de végétation
"""

__version__ = "1.0.0"
__author__ = "Ortho Processor Team"

# Imports conditionnels pour éviter les erreurs si les dépendances ne sont pas installées
try:
    from .downloader import OrthoDownloader
    from .converter import OrthoConverter
    from .vegetation_indices import VegetationIndicesCalculator
    from .thresholding import VegetationThresholder
    from .main_processor import OrthoProcessor

    __all__ = [
        "OrthoDownloader",
        "OrthoConverter",
        "VegetationIndicesCalculator",
        "VegetationThresholder",
        "OrthoProcessor",
    ]
except ImportError as e:
    print(f"⚠️  Certaines dépendances ne sont pas installées: {e}")
    print("📦 Installez les dépendances avec: pip install -r requirements.txt")
    __all__ = []
