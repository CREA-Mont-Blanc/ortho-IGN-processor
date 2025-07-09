"""
Module de téléchargement des données orthophotographiques
"""

import os
import glob
import requests
import subprocess
from pathlib import Path
from typing import List, Dict, Optional


class OrthoDownloader:
    """Gestionnaire de téléchargement des données orthophotographiques"""

    def __init__(self, base_dir: str):
        """
        Initialise le téléchargeur

        Args:
            base_dir: Répertoire de base pour stocker les données
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def load_urls_from_file(self, urls_file: str) -> Dict[str, Dict[str, List[str]]]:
        """
        Charge les URLs depuis un fichier texte

        Format du fichier:
        D073
        RVB
        https://data.geopf.fr/telechargement/download/...
        https://data.geopf.fr/telechargement/download/...
        IRC
        https://data.geopf.fr/telechargement/download/...
        D038
        RVB
        ...

        Args:
            urls_file: Chemin vers le fichier contenant les URLs

        Returns:
            Dictionnaire structuré: {department: {band: [urls]}}
        """
        urls_data = {}
        current_dept = None
        current_band = None

        with open(urls_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                # Ignorer les lignes vides et les commentaires
                if not line or line.startswith("#"):
                    continue

                # Détecter un nouveau département (commence par D suivi de chiffres)
                if line.startswith("D") and line[1:].isdigit():
                    current_dept = line
                    if current_dept not in urls_data:
                        urls_data[current_dept] = {}

                # Détecter une nouvelle bande (RVB ou IRC)
                elif line.upper() in ["RVB", "IRC"]:
                    current_band = line.upper()
                    if current_dept and current_band not in urls_data[current_dept]:
                        urls_data[current_dept][current_band] = []

                # URL (commence par http)
                elif line.startswith("http") and current_dept and current_band:
                    urls_data[current_dept][current_band].append(line)

        return urls_data

    def download_department_data(
        self, department: str, bands: List[str] = None, urls_file: str = None
    ) -> Dict[str, List[str]]:
        """
        Télécharge les données pour un département donné

        Args:
            department: Numéro du département (ex: "74", "73")
            bands: Liste des bandes à télécharger (par défaut ["IRC", "RVB"])
            urls_file: Fichier contenant les URLs (optionnel)

        Returns:
            Dictionnaire avec les chemins des fichiers téléchargés par bande
        """
        if bands is None:
            bands = ["IRC", "RVB"]

        print(f"📥 Téléchargement des données pour le département {department}")

        downloaded_files = {}

        # Charger les URLs depuis le fichier si fourni
        if urls_file and os.path.exists(urls_file):
            urls_data = self.load_urls_from_file(urls_file)
            dept_key = f"D{department.zfill(3)}"  # Formatage D073, D074, etc.

            if dept_key in urls_data:
                for band in bands:
                    if band in urls_data[dept_key]:
                        print(
                            f"   📁 Téléchargement bande {band} ({len(urls_data[dept_key][band])} fichiers)"
                        )
                        band_dir = self.base_dir / department / band
                        band_dir.mkdir(parents=True, exist_ok=True)

                        # Télécharger chaque URL
                        for url in urls_data[dept_key][band]:
                            try:
                                self._download_with_resume(url, str(band_dir))
                            except Exception as e:
                                print(f"     ⚠️  Erreur pour {url}: {e}")

                        # Extraire les archives 7z si nécessaire
                        self._extract_7z_parts(str(band_dir))

                        # Lister les fichiers téléchargés
                        files = self._list_files_in_dir(band_dir)
                        downloaded_files[band] = files
                    else:
                        print(f"   ⚠️  Bande {band} non trouvée pour {dept_key}")
            else:
                print(f"   ⚠️  Département {dept_key} non trouvé dans le fichier URLs")
        else:
            # Mode simulation si pas de fichier URLs
            for band in bands:
                print(f"   Bande {band}...")
                band_dir = self.base_dir / department / band
                band_dir.mkdir(parents=True, exist_ok=True)

                files = self._list_files_in_dir(band_dir)
                downloaded_files[band] = files

        return downloaded_files

    def _download_with_resume(self, url: str, dest_dir: str):
        """
        Télécharge un fichier avec reprise en cas d'interruption

        Args:
            url: URL du fichier à télécharger
            dest_dir: Répertoire de destination
        """
        try:
            from tqdm import tqdm
        except ImportError:
            print("⚠️  tqdm non installé, pas de barre de progression")
            tqdm = None

        filename = url.split("/")[-1]
        file_path = os.path.join(dest_dir, filename)
        headers = {}
        file_exists = os.path.exists(file_path)
        downloaded = os.path.getsize(file_path) if file_exists else 0

        # Vérifier la taille du fichier distant
        try:
            with requests.head(url, timeout=30) as r:
                if r.status_code != 200:
                    print(f"     ❌ Erreur HEAD pour {filename}: {r.status_code}")
                    return
                total_size = int(r.headers.get("content-length", 0))

                # Fichier déjà complètement téléchargé
                if downloaded >= total_size and total_size > 0:
                    print(f"     ✅ Déjà téléchargé : {filename}")
                    return
        except requests.RequestException as e:
            print(f"     ⚠️  Impossible de vérifier {filename}: {e}")
            return

        # Téléchargement avec reprise
        headers["Range"] = f"bytes={downloaded}-"

        try:
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                if r.status_code not in [206, 200]:
                    print(f"     ❌ Erreur GET pour {filename}: code {r.status_code}")
                    return

                mode = "ab" if file_exists else "wb"

                if tqdm:
                    with open(file_path, mode) as f, tqdm(
                        total=total_size,
                        initial=downloaded,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        desc=filename,
                    ) as bar:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                bar.update(len(chunk))
                else:
                    # Sans barre de progression
                    with open(file_path, mode) as f:
                        print(f"     📥 Téléchargement {filename}...")
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    print(f"     ✅ Terminé : {filename}")

        except requests.RequestException as e:
            print(f"     ❌ Erreur de téléchargement pour {filename}: {e}")

    def _extract_7z_parts(self, folder: str):
        """
        Extrait automatiquement les archives 7z multi-parties

        Args:
            folder: Dossier contenant les parties d'archive
        """
        part001 = None
        for file in os.listdir(folder):
            if file.endswith(".7z.001"):
                part001 = os.path.join(folder, file)
                break

        if part001:
            print(f"     🗜️  Extraction depuis : {os.path.basename(part001)}")
            try:
                subprocess.run(
                    ["7z", "x", part001, f"-o{folder}", "-y"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(f"     ✅ Extraction terminée")
            except FileNotFoundError:
                print(
                    "     ❌ Erreur : '7z' n'est pas installé ou non accessible dans le PATH."
                )
            except subprocess.CalledProcessError as e:
                print(f"     ❌ Erreur lors de l'extraction : {e}")
        else:
            print(f"     ℹ️  Aucun fichier .7z.001 trouvé dans {folder}")

    def _list_files_in_dir(self, directory: Path) -> List[str]:
        """
        Liste tous les fichiers raster dans un répertoire

        Args:
            directory: Répertoire à scanner

        Returns:
            Liste des chemins de fichiers
        """
        files = []
        if directory.exists():
            # Chercher les fichiers JP2 et TIFF
            jp2_files = list(directory.glob("**/*.jp2"))
            tif_files = list(directory.glob("**/*.tif"))
            files = [str(f) for f in jp2_files + tif_files]
        return files

    def list_available_files(self, department: str) -> Dict[str, List[str]]:
        """
        Liste les fichiers déjà disponibles localement

        Args:
            department: Numéro du département

        Returns:
            Dictionnaire avec les fichiers par bande
        """
        dept_dir = self.base_dir / department
        if not dept_dir.exists():
            return {}

        files_by_band = {}
        for band_dir in dept_dir.iterdir():
            if band_dir.is_dir():
                band_name = band_dir.name
                files = []
                files.extend(list(band_dir.glob("**/*.jp2")))
                files.extend(list(band_dir.glob("**/*.tif")))
                files_by_band[band_name] = [str(f) for f in files]

        return files_by_band

    def get_stats(self, department: str) -> Dict:
        """
        Obtient les statistiques des fichiers téléchargés
        """
        files_by_band = self.list_available_files(department)

        stats = {
            "department": department,
            "total_files": sum(len(files) for files in files_by_band.values()),
            "bands": {},
        }

        for band, files in files_by_band.items():
            total_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
            stats["bands"][band] = {
                "file_count": len(files),
                "total_size_gb": total_size / (1024**3),
            }

        return stats
