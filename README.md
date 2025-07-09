# Processeur Orthophotographique Interactif

Un package Python interactif pour le traitement des données orthophotographiques, le calcul d'indices de végétation et la création de cartes thématiques.

## 🚀 Fonctionnalités

- **Téléchargement automatique** des données orthophotographiques
- **Conversion et fusion** des bandes IRC et RVB en images RGBNIR
- **Calcul optimisé** de 7 indices de végétation (NDVI, SAVI, EVI, AVI, BI_NIR, RATIO, BSI)
- **Analyse thématique interactive** avec seuillage personnalisé
- **Cartographie automatique** des zones d'ombre et rocailleuses
- **Interface en ligne de commande** intuitive

## 📦 Structure du Package

```
ortho_processor/
├── __init__.py              # Package principal
├── downloader.py            # Module de téléchargement
├── converter.py             # Module de conversion et fusion
├── vegetation_indices.py    # Calcul des indices de végétation
├── thresholding.py          # Seuillage et cartes thématiques
└── main_processor.py        # Processeur principal interactif
```

## 🛠️ Installation

```bash
# Dépendances requises
pip install rasterio fiona numpy tqdm joblib

# GDAL doit être installé séparément
# Ubuntu/Debian:
sudo apt-get install gdal-bin python3-gdal

# ou avec conda:
conda install -c conda-forge gdal rasterio fiona
```

## 🎯 Utilisation

### Lancement rapide

```bash
python run_ortho_processor.py
```

### Workflow interactif

Le programme vous guidera à travers toutes les étapes :

1. **Configuration**
   - Départements à traiter (ex: 74,73,38)
   - Résolution cible en mètres (ex: 2.0)
   - Shapefile de découpage (optionnel)
   - Nombre de processus parallèles

2. **Téléchargement/Vérification** des données orthophotographiques

3. **Conversion et fusion**
   - Conversion JP2 → TIFF
   - Rééchantillonnage à la résolution cible
   - Fusion des bandes IRC/RVB → RGBNIR
   - Création de mosaïques départementales

4. **Calcul des indices de végétation**
   - NDVI (Normalized Difference Vegetation Index)
   - SAVI (Soil Adjusted Vegetation Index)
   - EVI (Enhanced Vegetation Index)
   - AVI (Advanced Vegetation Index)
   - BI_NIR (Brightness Index NIR)
   - RATIO (NIR/RGB Ratio)
   - BSI (Bare Soil Index)

5. **Analyse thématique interactive**
   - Affichage des statistiques des indices
   - Définition interactive des seuils
   - Création automatique des cartes thématiques
   - Génération d'un rapport de synthèse

### Exemple de seuillage

```
🌲 ZONE D'OMBRE (Végétation dense)
Condition 1: SAVI > 0.3
Condition 2: RATIO < 0.8

🪨 ZONE ROCAILLEUSE (Sol nu/rocheux)  
Condition 1: BSI > 0.1
Condition 2: NDVI < 0.2
```

## 📊 Indices de Végétation Calculés

| Indice | Formule | Description |
|--------|---------|-------------|
| **NDVI** | (NIR - Red) / (NIR + Red) | Indice de végétation normalisé |
| **SAVI** | (1 + L) × (NIR - Red) / (NIR + Red + L) | Ajusté pour les sols (L=0.5) |
| **EVI** | G × (NIR - Red) / (NIR + C1×Red - C2×Blue + L) | Végétation améliorée |
| **AVI** | [NIR × (1-Red) × (NIR-Red)]^(1/3) | Végétation avancée |
| **BI_NIR** | (Red + Green + Blue + NIR) / 4 | Indice de brillance |
| **RATIO** | NIR / (Red + Green + Blue) | Ratio simple NIR/RGB |
| **BSI** | ((Red+Green)+(NIR+Blue)) / ((Red+Green)-(NIR+Blue)) | Sol nu |

## 🗂️ Structure des Données de Sortie

```
base_dir/
├── raw_data/                    # Données brutes téléchargées
│   └── {dept}/
│       ├── IRC/                 # Bande infrarouge
│       └── RVB/                 # Bande rouge-vert-bleu
├── processed/                   # Données traitées
│   └── ORTHO_RGBNIR_*.tif      # Mosaïques finales
├── vegetation_indices/          # Indices de végétation
│   ├── NDVI.tif
│   ├── SAVI.tif
│   ├── EVI.tif
│   ├── AVI.tif
│   ├── BI_NIR.tif
│   ├── RATIO.tif
│   ├── BSI.tif
│   └── vegetation_indices_composite.tif
└── thematic_maps/              # Cartes thématiques
    ├── shadow_zone_map.tif     # Zones d'ombre
    ├── rocky_zone_map.tif      # Zones rocailleuses
    └── thematic_analysis_report.txt
```

## ⚡ Optimisations

- **Traitement par blocs** pour économiser la mémoire
- **Parallélisation** des conversions et fusions
- **Compression LZW** pour réduire la taille des fichiers
- **Support BigTIFF** pour les gros volumes
- **Gestion automatique** de la mémoire avec garbage collection

## 🔧 Personnalisation

### Ajout d'indices personnalisés

Modifiez la méthode `_compute_indices_block()` dans `vegetation_indices.py` :

```python
# Nouvel indice exemple
my_index = (nir * 2) / (red + green)
indices["MY_INDEX"] = my_index
```

### Modification des seuils par défaut

Vous pouvez créer des profils de seuillage prédéfinis dans `thresholding.py`.

## 📈 Statistiques Générées

Pour chaque indice calculé :
- Min, Max, Moyenne, Écart-type
- Percentiles (1%, 5%, 25%, 75%, 95%, 99%)

Pour chaque zone thématique détectée :
- Nombre de pixels détectés
- Pourcentage de couverture
- Surface en hectares et m²

## 🐛 Dépannage

### Erreurs courantes

1. **GDAL non trouvé** : Installer GDAL avec `conda install gdal`
2. **Mémoire insuffisante** : Réduire la taille des blocs dans le code
3. **CRS incompatibles** : Vérifier que raster et shapefile ont le même CRS

### Performance

- Utiliser un SSD pour améliorer les I/O
- Augmenter le nombre de processus selon votre CPU
- Surveiller l'utilisation mémoire avec `htop`

## 📝 Notes Techniques

- Support des formats JP2 et TIFF en entrée
- Projection recommandée : EPSG:2154 (Lambert 93)
- Résolutions testées : 0.5m à 10m
- Taille maximale testée : 100 Go par département

## 🤝 Contribution

Le code est modulaire et facilement extensible. Chaque module peut être utilisé indépendamment.

## 📄 Licence

Code libre pour usage scientifique et éducatif.
