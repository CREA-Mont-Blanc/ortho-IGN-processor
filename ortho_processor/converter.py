"""
Module de conversion et fusion des données orthophotographiques
"""

import os
import subprocess
import glob
from pathlib import Path
from typing import List, Dict, Tuple
import rasterio
from rasterio.enums import Resampling
from joblib import Parallel, delayed


class OrthoConverter:
    """Gestionnaire de conversion et fusion des fichiers orthophotographiques"""

    def __init__(self, input_dir: str, output_dir: str):
        """
        Initialise le convertisseur

        Args:
            input_dir: Répertoire contenant les données brutes
            output_dir: Répertoire de sortie pour les données traitées
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert_jp2_to_tif(self, jp2_path: str, target_resolution: float = 2.0) -> str:
        """
        Convertit un fichier JP2 en TIFF avec rééchantillonnage

        Args:
            jp2_path: Chemin vers le fichier JP2
            target_resolution: Résolution cible en mètres

        Returns:
            Chemin vers le fichier TIFF créé
        """
        array, meta = self._read_raster(jp2_path)

        # Calcul du facteur de mise à l'échelle
        original_res_x, original_res_y = meta["transform"][0], -meta["transform"][4]
        scale_x = original_res_x / target_resolution
        scale_y = original_res_y / target_resolution

        new_width = int(meta["width"] * scale_x)
        new_height = int(meta["height"] * scale_y)

        # Redimensionner le tableau
        with rasterio.open(jp2_path) as src:
            data = src.read(
                out_shape=(src.count, new_height, new_width),
                resampling=Resampling.lanczos,
            )
            transform = src.transform * src.transform.scale(
                (src.width / new_width), (src.height / new_height)
            )

        # Mise à jour des métadonnées
        meta.update(
            {
                "driver": "GTiff",
                "compress": "PACKBITS",
                "height": new_height,
                "width": new_width,
                "transform": transform,
            }
        )

        # Écriture du fichier TIFF
        output_path = jp2_path.replace(".jp2", f"_{target_resolution}m.tif")
        with rasterio.open(output_path, "w", **meta) as dst:
            dst.write(data)

        return output_path

    def convert_department_files(
        self, department: str, target_resolution: float = 2.0, n_jobs: int = 4
    ) -> Dict[str, List[str]]:
        """
        Convertit tous les fichiers JP2 d'un département

        Args:
            department: Numéro du département
            target_resolution: Résolution cible en mètres
            n_jobs: Nombre de processus parallèles

        Returns:
            Dictionnaire avec les fichiers convertis par bande
        """
        print(f"🔄 Conversion des fichiers JP2 pour le département {department}")

        converted_files = {}

        for band in ["IRC", "RVB"]:
            folder = self.input_dir / department / band
            if not folder.exists():
                print(f"   ⚠️  Dossier {folder} non trouvé")
                continue

            print(f"   Traitement de la bande {band}")

            jp2_files = list(folder.glob("**/*.jp2"))
            existing_tif = list(folder.glob("**/*.tif"))

            # Filtrer les fichiers déjà convertis
            jp2_to_convert = [
                str(jp2)
                for jp2 in jp2_files
                if str(jp2).replace(".jp2", f"_{target_resolution}m.tif")
                not in [str(t) for t in existing_tif]
            ]

            if not jp2_to_convert:
                print(f"      ✅ Tous les fichiers déjà convertis")
                converted_files[band] = [str(f) for f in existing_tif]
                continue

            print(f"      📝 Conversion de {len(jp2_to_convert)} fichiers")

            # Conversion parallèle
            converted = Parallel(n_jobs=n_jobs)(
                delayed(self.convert_jp2_to_tif)(jp2, target_resolution)
                for jp2 in jp2_to_convert
            )

            # Ajouter les fichiers existants
            all_tif = list(folder.glob("**/*.tif"))
            converted_files[band] = [str(f) for f in all_tif]

        return converted_files

    def merge_bands(
        self,
        irc_files: List[str],
        rvb_files: List[str],
        target_resolution: float = 2.0,
        n_jobs: int = 4,
    ) -> List[str]:
        """
        Fusionne les bandes IRC et RVB pour créer des images RGBNIR

        Args:
            irc_files: Liste des fichiers IRC
            rvb_files: Liste des fichiers RVB
            target_resolution: Résolution cible
            n_jobs: Nombre de processus parallèles

        Returns:
            Liste des fichiers RGBNIR créés
        """
        print(f"🔗 Fusion des bandes IRC et RVB")

        # Préparation des répertoires
        work_dir = self.output_dir / "processed"
        work_dir.mkdir(exist_ok=True)

        uint16_dir = work_dir / "uint16_raw"
        merged_dir = work_dir / "merged"
        uint16_dir.mkdir(exist_ok=True)
        merged_dir.mkdir(exist_ok=True)

        # Conversion en uint16
        print("   📊 Conversion en uint16...")
        all_files = irc_files + rvb_files
        Parallel(n_jobs=n_jobs)(
            delayed(self._gdal_translate)(file_path, str(uint16_dir))
            for file_path in all_files
        )

        # Fusion des bandes
        print("   🎯 Fusion des bandes...")
        uint16_files = sorted(list(uint16_dir.glob("*_16bits.tif")))

        merged_files = Parallel(n_jobs=n_jobs)(
            delayed(self._merge_bands_pair)(
                uint16_files[i : i + 2], str(merged_dir), target_resolution
            )
            for i in range(0, len(uint16_files), 2)
        )

        return [f for f in merged_files if f is not None]

    def create_final_mosaic(
        self, rgbnir_files: List[str], department: str, target_resolution: float = 2.0
    ) -> str:
        """
        Crée la mosaïque finale à partir des fichiers RGBNIR

        Args:
            rgbnir_files: Liste des fichiers RGBNIR
            department: Numéro du département
            target_resolution: Résolution

        Returns:
            Chemin vers la mosaïque finale
        """
        print(f"🗺️  Création de la mosaïque finale")

        name_r = str(target_resolution).replace(".", "M")
        output_path = (
            self.output_dir / f"ORTHO_RGBNIR_{name_r}_EPSG2154_D{department}.tif"
        )

        # Afficher la taille totale
        total_size = sum(os.path.getsize(f) for f in rgbnir_files if os.path.exists(f))
        print(f"   📏 Taille totale des fichiers: {total_size/(1024**3):.2f} Go")

        cmd = [
            "gdal_merge.py",
            "-ot",
            "UInt16",
            "-of",
            "GTiff",
            "-co",
            "BIGTIFF=YES",
            "-co",
            "COMPRESS=DEFLATE",
            "-co",
            "PREDICTOR=2",
            "-o",
            str(output_path),
            *rgbnir_files,
        ]

        subprocess.run(cmd, check=True)
        print(f"   ✅ Mosaïque créée: {output_path}")

        return str(output_path)

    def _read_raster(self, file_path: str) -> Tuple:
        """Lit un fichier raster et retourne les données et métadonnées"""
        with rasterio.open(file_path) as src:
            return src.read(), src.meta

    def _gdal_translate(self, file_path: str, out_dir: str):
        """Convertit un fichier en uint16"""
        out_file = os.path.join(
            out_dir, os.path.basename(file_path).replace(".tif", "_16bits.tif")
        )

        if os.path.exists(out_file):
            return

        cmd = [
            "gdal_translate",
            "-ot",
            "UInt16",
            "-scale",
            "0",
            "255",
            "0",
            "65535",
            "-of",
            "GTiff",
            "-co",
            "BIGTIFF=YES",
            file_path,
            out_file,
        ]
        subprocess.run(cmd, check=True)

    def _merge_bands_pair(
        self, file_pair: List[str], out_dir: str, resolution: float
    ) -> str:
        """Fusionne une paire de fichiers IRC/RVB"""
        if len(file_pair) != 2:
            return None

        # Déterminer quel fichier est IRC et lequel est RVB
        i, j = file_pair
        if "IRC" in i:
            irc, rvb = i, j
        else:
            irc, rvb = j, i

        base_name = os.path.basename(rvb)[:27]
        dir_m = os.path.join(out_dir, base_name)
        os.makedirs(dir_m, exist_ok=True)

        # Créer les bandes individuelles puis les fusionner
        self._create_individual_bands(irc, rvb, dir_m)

        # Créer le fichier RGBNIR final
        output_file = os.path.join(
            dir_m,
            base_name.replace("0M20", str(resolution).replace(".", "M"))
            + "_RGBNIR.tif",
        )

        if not os.path.exists(output_file):
            rgbnir_temp = os.path.join(dir_m, base_name + "_RGBNIR.tif")
            self._create_rgbnir_composite(dir_m, base_name, rgbnir_temp)
            self._resample_to_target_resolution(rgbnir_temp, output_file, resolution)

        return output_file

    def _create_individual_bands(self, irc_file: str, rvb_file: str, output_dir: str):
        """Crée les bandes individuelles B, R, G, NIR"""
        base_name = os.path.basename(rvb_file)[:27]

        # Bande B (Bleu)
        b_file = os.path.join(output_dir, f"{base_name}_B_B4.tif")
        if not os.path.exists(b_file):
            cmd = ["gdal_translate", "-ot", "UInt16", "-b", "3", rvb_file, b_file]
            subprocess.run(cmd, check=True)

        # Bande NIR
        nir_file = os.path.join(output_dir, f"{base_name}_NIR_B1.tif")
        if not os.path.exists(nir_file):
            cmd = ["gdal_translate", "-ot", "UInt16", "-b", "1", irc_file, nir_file]
            subprocess.run(cmd, check=True)

        # Bandes R et G (moyennes)
        for band_info in [("R", "B2", "1", "2"), ("G", "B3", "2", "3")]:
            band_name, band_code, rvb_band, irc_band = band_info
            output_file = os.path.join(
                output_dir, f"{base_name}_{band_name}_{band_code}.tif"
            )

            if not os.path.exists(output_file):
                cmd = [
                    "gdal_calc.py",
                    "--type=UInt16",
                    "-A",
                    rvb_file,
                    f"--A_band={rvb_band}",
                    "-B",
                    irc_file,
                    f"--B_band={irc_band}",
                    "--outfile",
                    output_file,
                    "--calc",
                    "(A/2) + (B/2)",
                    "--NoDataValue=0",
                ]
                subprocess.run(cmd, check=True)

    def _create_rgbnir_composite(self, dir_path: str, base_name: str, output_file: str):
        """Crée le composite RGBNIR"""
        if os.path.exists(output_file):
            return

        nir_file = os.path.join(dir_path, f"{base_name}_NIR_B1.tif")
        r_file = os.path.join(dir_path, f"{base_name}_R_B2.tif")
        g_file = os.path.join(dir_path, f"{base_name}_G_B3.tif")
        b_file = os.path.join(dir_path, f"{base_name}_B_B4.tif")

        cmd = [
            "gdal_merge.py",
            "-separate",
            "-ot",
            "UInt16",
            "-of",
            "GTiff",
            "-co",
            "BIGTIFF=YES",
            "-o",
            output_file,
            nir_file,
            r_file,
            g_file,
            b_file,
        ]
        subprocess.run(cmd, check=True)

    def _resample_to_target_resolution(
        self, input_file: str, output_file: str, resolution: float
    ):
        """Rééchantillonne à la résolution cible"""
        if os.path.exists(output_file):
            return

        cmd = [
            "gdal_translate",
            "-of",
            "GTiff",
            "-co",
            "BIGTIFF=YES",
            "-tr",
            str(resolution),
            str(resolution),
            "-r",
            "lanczos",
            "-ot",
            "UInt16",
            input_file,
            output_file,
        ]
        subprocess.run(cmd, check=True)
