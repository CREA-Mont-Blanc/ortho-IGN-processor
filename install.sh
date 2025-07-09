#!/bin/bash

# Script d'installation du processeur orthophotographique

echo "🚀 INSTALLATION DU PROCESSEUR ORTHOPHOTOGRAPHIQUE"
echo "=================================================="

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

echo "✅ Python 3 détecté: $(python3 --version)"

# Vérifier pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 n'est pas installé"
    exit 1
fi

echo "✅ pip3 détecté"

# Installer les dépendances système (Ubuntu/Debian)
echo ""
echo "📦 Installation des dépendances système..."

if command -v apt-get &> /dev/null; then
    echo "🔧 Détection d'Ubuntu/Debian, installation via apt-get..."
    sudo apt-get update
    sudo apt-get install -y gdal-bin python3-gdal python3-dev build-essential
elif command -v yum &> /dev/null; then
    echo "🔧 Détection de CentOS/RHEL, installation via yum..."
    sudo yum install -y gdal gdal-devel gdal-python3
elif command -v brew &> /dev/null; then
    echo "🔧 Détection de macOS, installation via Homebrew..."
    brew install gdal
else
    echo "⚠️  Système non reconnu. Veuillez installer GDAL manuellement."
fi

# Installer les dépendances Python
echo ""
echo "🐍 Installation des dépendances Python..."

pip3 install --upgrade pip
pip3 install -r requirements.txt

# Vérifier l'installation
echo ""
echo "🔍 Vérification de l'installation..."

python3 -c "import rasterio; print('✅ rasterio:', rasterio.__version__)" 2>/dev/null || echo "❌ rasterio non installé"
python3 -c "import fiona; print('✅ fiona:', fiona.__version__)" 2>/dev/null || echo "❌ fiona non installé"
python3 -c "import numpy; print('✅ numpy:', numpy.__version__)" 2>/dev/null || echo "❌ numpy non installé"
python3 -c "import tqdm; print('✅ tqdm installé')" 2>/dev/null || echo "❌ tqdm non installé"
python3 -c "import joblib; print('✅ joblib installé')" 2>/dev/null || echo "❌ joblib non installé"

# Test GDAL
echo ""
echo "🗺️  Test GDAL..."
if command -v gdalinfo &> /dev/null; then
    echo "✅ GDAL disponible: $(gdalinfo --version)"
else
    echo "❌ GDAL non disponible en ligne de commande"
fi

# Test du package
echo ""
echo "🧪 Test du package..."
python3 -c "
try:
    from ortho_processor import OrthoProcessor
    print('✅ Package ortho_processor importé avec succès')
except Exception as e:
    print(f'❌ Erreur d\\'importation: {e}')
"

echo ""
echo "🎉 INSTALLATION TERMINÉE!"
echo ""
echo "📚 PROCHAINES ÉTAPES:"
echo "  1. Testez avec: python3 test_demo.py"
echo "  2. Utilisez avec: python3 run_ortho_processor.py"
echo "  3. Consultez le README.md pour la documentation"
echo ""
echo "🆘 EN CAS DE PROBLÈME:"
echo "  - Vérifiez que GDAL est correctement installé"
echo "  - Redémarrez votre terminal après l'installation"
echo "  - Consultez les logs d'erreur ci-dessus"
