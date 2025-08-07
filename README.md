# Package de Traitement Orthophotographique

## Contexte et Objectifs

### Objectif Principal

L'idée de ce package est de traiter les données orthophotographiques de l'IGN sur des zones montagneuses pour en extraire des masques de rocaille destinés à être utilisés sur les données LiDAR pour évaluer la végétation. Ce but n'est pas le seul : à partir des informations des orthos, on peut réaliser de nombreuses analyses.

### Masques Générés

Le package génère potentiellement deux masques essentiels :

1. **Masque de Rocaille** : Identification des surfaces minérales et sols nus
2. **Masque d'Ombre** : Nécessaire car en milieu montagneux, lors des acquisitions aériennes (couramment en juillet), les ombres portées rendent impossible la différenciation entre un caillou et un arbre dans une zone ombragée

### Approche Technique

L'idée était de rassembler les 4 bandes (Rouge, Vert, Bleu, NIR) dans un seul fichier pour réaliser facilement des calculs d'indicateurs. 

**Important :** Les données orthophotographiques sont normalisées pour la visualisation, donc les valeurs ne sont pas liées à la physique du signal et de la cible considérée. Ainsi, les indicateurs construits ne sont pas fidèlement représentatifs de la valeur attendue (comme par exemple pour le NDVI) mais restent de bons proxys pour distinguer des zones.

### Perspectives d'Évolution

1. **Calibration Radiométrique** : Faire un matching entre les données ortho et des données satellitaires (type Sentinel-2) pour calibrer correctement les données en termes physiques
2. **Classification Fine** : Utiliser les données 4 bandes ou les transformations d'indicateurs pour faire de la classification fine (on peut descendre à 0.5m de résolution)
3. **Validation et Apprentissage** : Pour faire les choses bien, il faudrait valider ou éventuellement apprendre à partir de bases de données sur certaines zones quels sont les seuils optimaux dans quelles représentations pour détecter la rocaille, afin d'affiner l'existant à une résolution très fine

## Caractéristiques des Données Orthophotographiques

### Spécifications Techniques

Les données orthophotographiques traitées par ce package ont les caractéristiques suivantes :

- **Résolution spatiale native** : 50 cm
- **Bandes spectrales** : RVB (Rouge-Vert-Bleu) + IRC (Infrarouge-Rouge-Vert)  
- **Format de distribution** : Archives 7z multi-parties (standard IGN)
- **Projection** : EPSG:2154 (Lambert 93)

### Données par Département

#### Haute-Savoie (74)
- **Période d'acquisition** : 22 août 2023 au 10 septembre 2023
- **Volume compressé** : 41 GB (archives 7z pour RVB et NIR)
- **Fichiers décompressés** : 476 fichiers
- **Volume après downsampling à 2m** : 7.6 GB

#### Savoie (73)  
- **Période d'acquisition** : 11 août 2024 au 30 août 2024
- **Volume compressé** : 55 GB (archives 7z pour RVB et NIR)
- **Fichiers décompressés** : 614 fichiers  
- **Volume après downsampling à 2m** : 10.6 GB

#### Isère (38)
- **Période d'acquisition** : 30 juillet 2024 au 11 août 2024
- **Fichiers décompressés** : 766 fichiers
- **Volume après downsampling à 2m** : 13.8 GB

### Implications Techniques

**Taille des données originales :** La résolution native de 50 cm génère des volumes de données très importants. Le downsampling à 2m permet de réduire significativement l'empreinte disque tout en conservant une résolution suffisante pour l'analyse de végétation et la détection de rocaille.

**Périodes d'acquisition estivales :** Les acquisitions en juillet-août-septembre correspondent aux conditions optimales de végétation en milieu montagneux, mais génèrent également les problématiques d'ombres portées nécessitant un masque spécifique.

## Présentation

Ce package Python permet le traitement automatisé et interactif des données orthophotographiques, du téléchargement au calcul d'indices de végétation et à la génération de cartes thématiques. Il est conçu pour traiter de gros volumes de données de manière optimisée et modulaire.

## Architecture du Package

### Structure Modulaire

Le package `ortho_processor` est organisé en six modules spécialisés :

```bash
ortho_processor/
├── __init__.py              # Point d'entrée du package
├── config.py               # Configuration et profils prédéfinis
├── downloader.py            # Gestion du téléchargement des données
├── converter.py             # Conversion JP2→TIFF et fusion des bandes  
├── vegetation_indices.py    # Calcul optimisé des indices de végétation
├── thresholding.py          # Seuillage et cartes thématiques
└── main_processor.py        # Orchestrateur principal du workflow
```

### Flux de Traitement

Le workflow s'organise en séquences logiques :

1. **Configuration utilisateur** → Saisie des paramètres de traitement
2. **Téléchargement de données** → Récupération des archives orthophotographiques
3. **Extraction et conversion** → JP2 vers TIFF avec rééchantillonnage
4. **Fusion des bandes** → Création d'images RGBNIR
5. **Calcul d'indices** → 7 indices de végétation optimisés
6. **Analyse thématique** → Seuillage interactif et cartographie
7. **Génération de rapports** → Synthèse statistique et résultats

## Installation et Configuration

### Dépendances Système

Le package nécessite GDAL comme dépendance système critique :

```bash
# Ubuntu/Debian
sudo apt-get install gdal-bin python3-gdal libgdal-dev

# Vérification de 7z pour l'extraction d'archives
sudo apt-get install p7zip-full

# Alternative avec conda (recommandé)
conda install -c conda-forge gdal rasterio fiona
```

### Dépendances Python

```bash
pip install rasterio fiona numpy tqdm joblib shapely
```

### Variables d'Environnement

Configuration nécessaire pour GDAL :

```bash
export GDAL_DATA=/usr/share/gdal
export PROJ_LIB=/usr/share/proj
```

## Configuration et Paramétrage

### Fichiers de Configuration Externe

#### Fichier URLs (urls_ortho.txt)

Format structuré pour définir les sources de téléchargement :

```
# Commentaires commençant par #
D{numero_departement}
{BANDE}
{URL1}
{URL2}
...

# Exemple :
D038
RVB
https://data.geopf.fr/telechargement/download/BDORTHO/BDORTHO_2-0_RVB-0M20_JP2-E080_LAMB93_D038_2024-01-01/BDORTHO_2-0_RVB-0M20_JP2-E080_LAMB93_D038_2024-01-01.7z.001
https://data.geopf.fr/telechargement/download/BDORTHO/BDORTHO_2-0_RVB-0M20_JP2-E080_LAMB93_D038_2024-01-01/BDORTHO_2-0_RVB-0M20_JP2-E080_LAMB93_D038_2024-01-01.7z.002

IRC
https://data.geopf.fr/telechargement/download/BDORTHO/BDORTHO_2-0_IRC-0M20_JP2-E080_LAMB93_D038_2024-01-01/BDORTHO_2-0_IRC-0M20_JP2-E080_LAMB93_D038_2024-01-01.7z.001
```

**Règles de formatage :**
- Les départements suivent le format `D{XXX}` avec zéro initial (D038, D073, D074)
- Les bandes acceptées sont `RVB` (Rouge-Vert-Bleu) et `IRC` (Infrarouge-Rouge-Vert)
- Une URL par ligne, sans espaces ni caractères spéciaux
- Les commentaires commencent par `#` et sont ignorés

### Profils de Seuillage Prédéfinis

Le fichier `config.py` contient des profils prêts à utiliser :

#### Profils Disponibles

```python
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
    }
}
```

#### Valeurs Recommandées par Indice

```python
RECOMMENDED_RANGES = {
    "NDVI": {
        "min": -1.0, "max": 1.0,
        "vegetation_min": 0.2, "vegetation_high": 0.8,
        "water_max": 0.0, "soil_max": 0.2,
    },
    "SAVI": {
        "min": -1.5, "max": 1.5,
        "vegetation_min": 0.2, "vegetation_high": 0.6,
        "soil_max": 0.1,
    },
    "BSI": {
        "min": -1.0, "max": 1.0,
        "bare_soil_min": 0.1, "vegetation_max": -0.1,
    }
}
```

## Étape 1 : Configuration du Workflow

### Paramètres Utilisateur

Le workflow interactif demande :

1. **Départements à traiter** : Format `XX,YY,ZZ` (ex: `74,73,38`)
2. **Résolution cible** : En mètres (0.5 à 10.0m, recommandé : 2.0m)  
3. **Fichier URLs** : Chemin vers le fichier de configuration des téléchargements
4. **Shapefile de découpage** : Optionnel, pour limiter la zone d'étude
5. **Nombre de processus parallèles** : Selon les capacités CPU (1 à 8)

### Justification des Choix de Configuration

**Résolution cible :** La résolution de 2.0m représente un bon compromis entre précision spatiale et volume de données. Les résolutions plus fines (0.5m) génèrent des fichiers très volumineux, tandis que les résolutions plus grossières (>5m) perdent en précision pour l'analyse de végétation.

**Parallélisation :** Le nombre de processus est limité par la mémoire disponible. Chaque processus traite un bloc de données indépendamment, ce qui permet une accélération linéaire jusqu'à saturation des ressources système.

## Étape 2 : Téléchargement des Données

### Module downloader.py

#### Fonctionnalités

- **Téléchargement avec reprise** : Les téléchargements interrompus reprennent automatiquement
- **Gestion des archives multi-parties** : Extraction automatique des fichiers .7z.001, .7z.002, etc.
- **Validation des téléchargements** : Vérification de la taille des fichiers
- **Organisation automatique** : Structure de dossiers par département et bande

#### Format des Archives

Les données orthophotographiques françaises sont distribuées par l'IGN sous forme d'archives 7-Zip multi-parties, ce qui est le standard IGN car il y a beaucoup de fichiers JP2 compressés :
- Fichiers `.7z.001`, `.7z.002`, ... jusqu'à `.7z.XXX`
- L'extraction nécessite l'outil système `7z`
- Le processus d'extraction est automatisé et détecte le premier fichier (.001)

#### Structure de Données Créée

```
base_dir/raw_data/
├── 038/                    # Département Isère
│   ├── RVB/               # Bande Rouge-Vert-Bleu
│   │   ├── *.jp2         # Fichiers JPEG2000 extraits
│   │   └── *.7z.001      # Archives téléchargées
│   └── IRC/               # Bande Infrarouge-Rouge-Vert
│       ├── *.jp2
│       └── *.7z.001
├── 073/                   # Département Savoie
└── 074/                   # Département Haute-Savoie
```

#### Gestion des Erreurs de Téléchargement

- **Timeout** : 30 secondes par requête
- **Retry automatique** : 3 tentatives par fichier
- **Validation de taille** : Comparaison avec les headers HTTP
- **Logging détaillé** : Suivi des erreurs et succès

## Étape 3 : Conversion et Fusion

### Module converter.py

#### Conversion JP2 vers TIFF

**Justification du choix :** Il est plus simple de manipuler les fichiers TIFF fusionnés que les JP2. Les fichiers JPEG2000 (.jp2) sont compressés et tuilés, mais décompresser le résultat est très volumineux. Avec une résolution initiale de 50cm, il faut soit assez de place sur disque, soit nécessairement downsampler les résultats pour être stockés et manipulés. La conversion permet :
- Manipulation plus directe des données fusionnées  
- Meilleure compatibilité avec les outils de traitement
- Possibilité d'optimisation avec compression LZW
- Gestion plus efficace des opérations sur les données multi-bandes

#### Rééchantillonnage

Utilise l'algorithme de rééchantillonnage bilinéaire pour ajuster la résolution spatiale :
- **Méthode** : `Resampling.bilinear` de GDAL
- **Préservation** : Conservation du système de coordonnées et de l'étendue géographique
- **Optimisation** : Traitement par blocs pour économiser la mémoire

#### Fusion des Bandes IRC et RVB

Le processus crée des images RGBNIR (4 bandes) :

1. **Lecture des métadonnées** : CRS, transformation géospatiale, nodata
2. **Vérification de cohérence** : Même emprise, résolution, projection
3. **Fusion pixel par pixel** : 
   - Bande 1 (Rouge) : NIR de IRC
   - Bande 2 (Rouge) : Rouge de RVB  
   - Bande 3 (Vert) : Vert de RVB
   - Bande 4 (Bleu) : Bleu de RVB

#### Gestion des Types de Données

- **Entrée** : uint16 (0-65535) pour préserver la précision radiométrique originale
- **Normalisation** : Conversion en float32 (0.0-1.0) pour les calculs d'indices
- **Masquage** : Gestion des valeurs nodata et aberrantes

#### Configuration des Fichiers de Sortie

```python
profile = {
    'driver': 'GTiff',
    'dtype': 'uint16',      # Préservation de la précision
    'nodata': 0,
    'width': width,
    'height': height,
    'count': 4,             # RGBNIR
    'crs': 'EPSG:2154',    # Lambert 93 (France)
    'transform': transform,
    'compress': 'lzw',      # Compression sans perte
    'BIGTIFF': 'YES'       # Support des fichiers > 4GB
}
```

### Convention de Nommage

```
ORTHO_RGBNIR_{resolution}m_EPSG{crs}_D{dept}.tif
```

Exemple : `ORTHO_RGBNIR_2.0m_EPSG2154_D074.tif`

## Étape 4 : Calcul des Indices de Végétation

### Module vegetation_indices.py

#### Indices Calculés

Le package calcule 7 indices de végétation spécialisés :

| Indice | Nom Complet | Formule | Plage | Usage Principal |
|--------|-------------|---------|-------|----------------|
| **NDVI** | Normalized Difference Vegetation Index | `(NIR - Red) / (NIR + Red)` | [-1, 1] | Détection générale de végétation |
| **SAVI** | Soil Adjusted Vegetation Index | `(1 + L) × (NIR - Red) / (NIR + Red + L)` | [-1.5, 1.5] | Végétation avec correction sol (L=0.5) |
| **EVI** | Enhanced Vegetation Index | `G × (NIR - Red) / (NIR + C1×Red - C2×Blue + L)` | [-1, 1] | Végétation dense, moins saturé |
| **AVI** | Advanced Vegetation Index | `[NIR × (1-Red) × (NIR-Red)]^(1/3)` | [-2, 2] | Végétation avec racine cubique |
| **BI_NIR** | Brightness Index with NIR | `(Red + Green + Blue + NIR) / 4` | [0, 1] | Indice de brillance générale |
| **RATIO** | NIR/RGB Ratio | `NIR / (Red + Green + Blue)` | [0, ∞] | Ratio simple NIR sur visible |
| **BSI** | Bare Soil Index | `((Red+Green)+(NIR+Blue)) / ((Red+Green)-(NIR+Blue))` | [-∞, ∞] | Détection des sols nus |

#### Justification du Choix des Indices

Les indicateurs ont été sélectionnés ou adaptés à partir de la base de données d'indices disponible sur [Index Database](https://www.indexdatabase.de/db/is.php?sensor_id=96), avec un accent sur ceux qui reflètent une sensibilité à la végétation ou à la rocaille. Diverses sources ont ainsi été utilisées et les formules ont dû être adaptées dans le cas où les bandes variaient légèrement, toujours dans l'optique d'avoir un premier proxy pour la distinction des zones rocailleuses.

**Sélection spécifique :**
- **NDVI et SAVI** : Indices de référence pour la végétation, SAVI corrige l'influence du sol visible
- **EVI** : Moins saturé que NDVI pour les forêts denses, intègre la correction atmosphérique  
- **BSI** : Spécialisé dans la détection des sols nus et surfaces minérales (objectif rocaille)
- **BI_NIR et RATIO** : Indices complémentaires pour détecter zones sombres et brillantes (gestion des ombres)
- **AVI** : Formulation avancée avec racine cubique, sensible aux faibles niveaux de végétation

**Note importante :** Étant donné la normalisation des données orthophotographiques pour la visualisation, ces indices servent de proxys relatifs plutôt que de mesures physiques absolues.

#### Traitement Optimisé par Blocs

**Taille de bloc** : 2048×2048 pixels (16 MB par bande en uint16)

**Justification de cette taille :** Pour gérer les fichiers en minimisant l'empreinte mémoire, une solution a été de gérer les données par blocs. Le choix de 2048 pixels est empirique. Une taille de 4096 pixels fonctionne aussi, mais le choix dépend de la configuration du PC et de la mémoire disponible :
- Compromis optimal entre performance et mémoire pour la plupart des configurations
- Compatible avec les configurations standard (8-16 GB RAM)  
- Permet la parallélisation sans surcharge excessive
- Ajustable selon les ressources disponibles

#### Gestion des Valeurs Spéciales

```python
# Division par zéro
mask = denominator != 0
result = np.where(mask, numerator/denominator, 0)

# Racines négatives (pour AVI)
mask = expression >= 0
result = np.where(mask, np.cbrt(expression), 0)

# Valeurs aberrantes
mask = (data > 0) & (data < 65535)
result = np.where(mask, data, np.nan)
```

#### Statistiques Calculées

Pour chaque indice :
- **Statistiques de base** : min, max, moyenne, écart-type
- **Percentiles** : 1%, 5%, 25%, 75%, 95%, 99%
- **Histogrammes** : Distribution des valeurs
- **Masques de qualité** : Zones valides/invalides

### Fichiers de Sortie

```
vegetation_indices/
├── NDVI.tif                           # Indice NDVI (float32)
├── SAVI.tif                           # Indice SAVI (float32)  
├── EVI.tif                            # Indice EVI (float32)
├── AVI.tif                            # Indice AVI (float32)
├── BI_NIR.tif                         # Indice BI_NIR (float32)
├── RATIO.tif                          # Indice RATIO (float32)
├── BSI.tif                            # Indice BSI (float32)
└── vegetation_indices_composite.tif    # Composite 7 bandes
```

### Considérations sur les Données Orthophotographiques

**Normalisation des Données :** Les données orthophotographiques de l'IGN sont normalisées pour la visualisation. Par conséquent :
- Les valeurs ne sont pas directement liées à la physique du signal et de la cible considérée
- Les indicateurs construits ne sont pas fidèlement représentatifs des valeurs physiques attendues (comme le NDVI classique)
- Ils restent néanmoins de bons proxys pour distinguer les différents types de zones
- L'interprétation doit se faire en termes relatifs plutôt qu'absolus

**Contexte Montagnard :** En milieu montagneux, les ombres portées (acquisitions couramment en juillet) créent des zones où il est impossible de différencier un élément minéral d'un élément végétal, d'où la nécessité du masque d'ombre en complément du masque de rocaille.

## Étape 5 : Analyse Thématique et Seuillage

### Module thresholding.py

#### Principe du Seuillage Multi-Condition

Chaque zone thématique est définie par plusieurs conditions combinées avec un **ET logique** :

```python
conditions = [
    {"index": "NDVI", "operator": ">", "threshold": 0.4},
    {"index": "SAVI", "operator": ">", "threshold": 0.3}
]
```

#### Opérateurs de Comparaison

- `>` : Supérieur strict
- `<` : Inférieur strict  
- `>=` : Supérieur ou égal
- `<=` : Inférieur ou égal

#### Workflow Interactif de Seuillage

1. **Affichage des statistiques** : Min, max, percentiles pour chaque indice
2. **Suggestions de seuils** : Valeurs recommandées basées sur la littérature
3. **Saisie utilisateur** : Définition interactive des conditions
4. **Prévisualisation** : Calcul du nombre de pixels correspondants
5. **Validation** : Confirmation avant génération des cartes

#### Zones Thématiques Standard

**Zone d'Ombre (Végétation Dense)**
```
Conditions suggérées :
- SAVI > 0.3 (végétation significative)
- RATIO < 0.8 (zone sombre)
- BI_NIR < 0.4 (faible brillance)
```

**Zone Rocailleuse (Sol Nu)**
```
Conditions suggérées :
- BSI > 0.1 (sol visible)
- NDVI < 0.2 (peu de végétation)
- BI_NIR > 0.3 (surface claire)
```

### Format de Sortie des Cartes

Les cartes thématiques sont des rasters binaires :
- **Type** : uint8
- **Valeur 255** : Zone détectée (conditions satisfaites)
- **Valeur 0** : Zone non détectée
- **NoData** : Zones masquées dans les données originales

```
thematic_maps/
├── shadow_zone_map.tif              # Carte des zones d'ombre
├── rocky_zone_map.tif               # Carte des zones rocailleuses  
├── custom_zone_1_map.tif            # Zones personnalisées
└── thematic_analysis_report.txt     # Rapport de synthèse
```

## Étape 6 : Génération de Rapports

### Rapport de Synthèse

Le fichier `thematic_analysis_report.txt` contient :

#### Statistiques par Zone
```
=== ZONE D'OMBRE ===
Conditions appliquées:
  1. SAVI > 0.3
  2. RATIO < 0.8

Résultats:
- Pixels détectés: 1,245,678
- Pourcentage total: 23.4%
- Surface (hectares): 12,456.78
- Surface (m²): 124,567,800
```

#### Statistiques Globales
```
=== STATISTIQUES GLOBALES ===
- Pixels analysés: 5,324,167
- Pixels valides: 5,301,982 (99.6%)
- Pixels masqués: 22,185 (0.4%)
- Surface totale: 530.20 km²
```

## Configuration Avancée

### Optimisations Mémoire

#### Paramètres de Performance

```python
# Taille des blocs (mémoire vs performance)
BLOCK_SIZE = 2048  # Pixels, ajustable selon RAM disponible

# Nombre de processus parallèles  
N_JOBS = min(4, cpu_count())  # Maximum 4 pour éviter la saturation

# Type de compression
COMPRESS = "lzw"  # Bon compromis taille/vitesse
```

#### Surveillance des Ressources

```bash
# Mémoire et CPU
htop

# I/O disque
iotop

# Espace disque
df -h
```

### Gestion des Types de Données

Optimisation de l'utilisation mémoire selon les étapes :

- **Téléchargement** : Streaming avec buffers de 8KB
- **Conversion** : uint16 → float32 temporaire → uint16/float32 final  
- **Indices** : Calculs en float32 pour la précision
- **Cartes** : uint8 pour les masques binaires

### Support BigTIFF

Activation automatique pour les fichiers > 4GB :

```python
profile['BIGTIFF'] = 'YES'
```

## Utilisation

### Lancement Standard

```bash
python -m ortho_processor.main_processor
```

### Utilisation Programmatique

```python
from ortho_processor import OrthoProcessor

# Initialisation
processor = OrthoProcessor(base_dir="/path/to/workspace")

# Workflow complet
processor.run_interactive_workflow()

# Utilisation modulaire
downloader = processor.downloader
files = downloader.download_department_data("074", urls_file="urls.txt")
```

### Tests et Validation

#### Test Complet avec Données Synthétiques

```bash
python test_demo.py
```

Ce script :
- Génère des images RGBNIR synthétiques
- Calcule tous les indices de végétation
- Applique des seuils prédéfinis
- Génère un rapport de test

#### Tests Unitaires

```bash
python -m pytest tests/
```

## Structure des Données de Sortie

### Organisation Complète

```
workspace/
├── raw_data/                          # Données brutes téléchargées
│   ├── 038/
│   │   ├── RVB/*.jp2                 # Fichiers Rouge-Vert-Bleu
│   │   └── IRC/*.jp2                 # Fichiers Infrarouge-Rouge-Vert
│   ├── 073/
│   └── 074/
├── processed/                         # Données converties et fusionnées
│   ├── ORTHO_RGBNIR_2.0m_EPSG2154_D038.tif
│   ├── ORTHO_RGBNIR_2.0m_EPSG2154_D073.tif  
│   └── ORTHO_RGBNIR_2.0m_EPSG2154_D074.tif
├── vegetation_indices/                # Indices calculés
│   ├── NDVI.tif                      # Normalized Difference Vegetation Index
│   ├── SAVI.tif                      # Soil Adjusted Vegetation Index
│   ├── EVI.tif                       # Enhanced Vegetation Index
│   ├── AVI.tif                       # Advanced Vegetation Index  
│   ├── BI_NIR.tif                    # Brightness Index with NIR
│   ├── RATIO.tif                     # NIR/RGB Ratio
│   ├── BSI.tif                       # Bare Soil Index
│   └── vegetation_indices_composite.tif  # Composite 7 bandes
└── thematic_maps/                    # Cartes thématiques
    ├── shadow_zone_map.tif           # Zones d'ombre (255/0)
    ├── rocky_zone_map.tif            # Zones rocailleuses (255/0)
    ├── forest_zone_map.tif           # Zones forestières (255/0)
    └── thematic_analysis_report.txt   # Rapport détaillé
```

### Métadonnées des Fichiers

Tous les fichiers raster conservent :
- **CRS** : EPSG:2154 (Lambert 93)
- **Résolution** : Selon paramétrage utilisateur
- **Étendue** : Union des empires des fichiers sources
- **NoData** : Masquage cohérent des zones invalides

## Résolution de Problèmes

### Erreurs Courantes

#### GDAL non installé
```bash
ImportError: No module named 'osgeo'
```
**Solution :** Installer GDAL avec `conda install -c conda-forge gdal`

#### Mémoire insuffisante
```bash
MemoryError: Unable to allocate array
```
**Solution :** Réduire `BLOCK_SIZE` de 2048 à 1024 pixels

#### Archives corrompues
```bash
7z: Archive corrupted
```
**Solution :** Retélécharger les fichiers .7z concernés

#### CRS incompatibles
```bash
ValueError: CRS incompatibles entre raster et shapefile
```
**Solution :** Reprojeter le shapefile en EPSG:2154

### Optimisations de Performance

#### Stockage
- **SSD recommandé** : Amélioration des I/O de 3-5x
- **Espace disque** : Prévoir 2-3x la taille des données brutes
- **Réseau** : Bande passante stable pour les téléchargements

#### Système  
- **RAM minimum** : 16 GB (32/64 GB recommandés)
- **CPU** : Multicore recommandé pour la parallélisation

## Extensions et Personnalisations

### Ajout d'Indices Personnalisés

Modification du module `vegetation_indices.py` :

```python
def _compute_indices_block(self, nir, red, green, blue):
    indices = {}
    
    # Indices existants...
    
    # Nouvel indice personnalisé
    my_index = (nir * 2) / (red + green + 0.1)  # Éviter division par zéro
    indices["MY_INDEX"] = my_index
    
    return indices
```

### Nouveaux Profils de Seuillage

Ajout dans `config.py` :

```python
DEFAULT_THRESHOLDS["ma_zone_personnalisee"] = {
    "description": "Description de ma zone",
    "conditions": [
        {"index": "MY_INDEX", "operator": ">", "threshold": 1.5},
        {"index": "NDVI", "operator": ">", "threshold": 0.1},
    ],
}
```

### Support d'Autres Projections

Le package est actuellement optimisé pour le Lambert 93 (EPSG:2154) dans le cadre spécifique du traitement des orthophotos françaises et de leur formalisme. Il est toujours possible de convertir les résultats dans d'autres systèmes de projection :

```python
# Remplacer EPSG:2154 par votre projection
target_crs = "EPSG:32632"  # UTM 32N par exemple
```

## Notes Techniques

### Formats Supportés

- **Entrée** : JP2 (JPEG2000), TIFF, archives 7z multi-parties
- **Sortie** : GeoTIFF avec compression LZW
- **Shapefile** : Tous formats supportés par Fiona
- **Projections** : Toutes projections GDAL, optimisé pour EPSG:2154

### Limites Testées

- **Résolution** : 0.2m à 10m
- **Taille fichier** : Jusqu'à 100 GB par département  
- **Départements** : Testé sur 1 à 10 départements simultanés
- **Durée** : 2-48h selon volume et configuration matérielle

### Compatibilité

- **Python** : 3.8+
- **GDAL** : 3.0+
- **Système** : Linux (testé), Windows et macOS (partiellement testés)

## Maintenance

### Nettoyage Automatique

```python
import shutil
# Suppression des fichiers temporaires
shutil.rmtree(work_dir)
```

### Mise à Jour des Dépendances

```bash
pip list --outdated
pip install --upgrade rasterio fiona numpy tqdm joblib
```

### Monitoring

- **Logs** : Fichiers de log générés automatiquement
- **Progression** : Barres de progression avec tqdm
- **Erreurs** : Capture et logging détaillé des exceptions

## Licence et Contributions

Le code est libre pour usage scientifique et éducatif. Le package est modulaire et chaque composant peut être utilisé indépendamment selon les besoins spécifiques de traitement géospatial.
