"""
Module de calcul des indices de végétation
"""

import os
import gc
import numpy as np
import rasterio
from rasterio.merge import merge
from pathlib import Path
from typing import List, Dict, Tuple


class VegetationIndicesCalculator:
    """Calculateur d'indices de végétation optimisé mémoire"""

    def __init__(self, output_dir: str):
        """
        Initialise le calculateur

        Args:
            output_dir: Répertoire de sortie pour les indices
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir = self.output_dir / "temp_processing"
        self.work_dir.mkdir(exist_ok=True)

    def process_files(
        self, input_files: List[str], shapefile_path: str = None
    ) -> Dict[str, str]:
        """
        Traite les fichiers d'entrée et calcule les indices de végétation

        Args:
            input_files: Liste des fichiers RGBNIR
            shapefile_path: Chemin vers le shapefile de découpage (optionnel)

        Returns:
            Dictionnaire avec les chemins des indices calculés
        """
        print("🌱 Début du calcul des indices de végétation")

        # Étape 1: Découpage si shapefile fourni
        processed_files = input_files
        if shapefile_path:
            print("✂️  Découpage des fichiers avec le shapefile")
            processed_files = [
                self._crop_with_shapefile(file, shapefile_path) for file in input_files
            ]

        # Étape 2: Calculer les statistiques globales
        print("📊 Calcul des statistiques globales")
        global_stats = self._calculate_global_stats(processed_files)

        # Étape 3: Extraire et fusionner les bandes
        print("🔧 Extraction et fusion des bandes")
        merged_bands = self._extract_and_merge_bands(processed_files, global_stats)

        # Étape 4: Calculer les indices de végétation
        print("🧮 Calcul des indices de végétation")
        indices_paths = self._calculate_indices(merged_bands)

        print("✅ Calcul des indices terminé")
        return indices_paths

    def _crop_with_shapefile(self, raster_path: str, shapefile_path: str) -> str:
        """Découpe un raster avec un shapefile"""
        import fiona
        from rasterio.mask import mask

        with fiona.open(shapefile_path, "r") as shapefile:
            shapes = [feature["geometry"] for feature in shapefile]
            shapefile_crs = shapefile.crs

        with rasterio.open(raster_path) as src:
            if src.crs != shapefile_crs:
                raise ValueError("CRS incompatibles entre raster et shapefile")

            out_image, out_transform = mask(src, shapes, crop=True)
            out_meta = src.meta.copy()
            out_meta.update(
                {
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                }
            )

            base, ext = os.path.splitext(raster_path)
            output_path = base + "_cropped.tif"

            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(out_image)

        return output_path

    def _calculate_global_stats(self, files: List[str]) -> Dict:
        """Calcule les statistiques globales pour la normalisation"""
        global_stats = {
            "red": {"min": float("inf"), "max": float("-inf")},
            "green": {"min": float("inf"), "max": float("-inf")},
            "blue": {"min": float("inf"), "max": float("-inf")},
            "nir": {"min": float("inf"), "max": float("-inf")},
        }

        for filepath in files:
            if not os.path.exists(filepath):
                continue

            with rasterio.open(filepath) as src:
                for ji, window in src.block_windows(1):
                    bands_data = [src.read(i + 1, window=window) for i in range(4)]

                    band_names = ["nir", "red", "green", "blue"]  # Ordre RGBNIR

                    for band_name, band_data in zip(band_names, bands_data):
                        valid_mask = (band_data > 0) & (band_data < 65535)
                        if np.sum(valid_mask) > 0:
                            global_stats[band_name]["min"] = min(
                                global_stats[band_name]["min"],
                                np.min(band_data[valid_mask]),
                            )
                            global_stats[band_name]["max"] = max(
                                global_stats[band_name]["max"],
                                np.max(band_data[valid_mask]),
                            )
            gc.collect()

        return global_stats

    def _extract_and_merge_bands(
        self, files: List[str], global_stats: Dict
    ) -> Dict[str, str]:
        """Extrait et fusionne les bandes de tous les fichiers"""
        band_files = {"red": [], "green": [], "blue": [], "nir": []}

        # Extraire chaque bande de chaque fichier
        for filepath in files:
            if not os.path.exists(filepath):
                continue

            with rasterio.open(filepath) as src:
                profile = src.profile.copy()
                profile.update(
                    {
                        "count": 1,
                        "dtype": "uint16",
                        "compress": "lzw",
                        "BIGTIFF": "YES",
                    }
                )

                # Ordre des bandes: NIR, R, G, B
                band_mapping = {1: "nir", 2: "red", 3: "green", 4: "blue"}

                for band_idx, band_name in band_mapping.items():
                    output_path = (
                        self.work_dir / f"{Path(filepath).stem}_{band_name}.tif"
                    )

                    if not output_path.exists():
                        self._extract_normalize_band(
                            src, band_idx, band_name, output_path, global_stats, profile
                        )

                    band_files[band_name].append(str(output_path))

        # Fusionner chaque bande
        merged_bands = {}
        for band_name, files in band_files.items():
            if files:
                merged_path = self.work_dir / f"merged_{band_name}.tif"
                self._merge_band_files(files, merged_path, band_name)
                merged_bands[band_name] = str(merged_path)

        return merged_bands

    def _extract_normalize_band(
        self,
        src,
        band_idx: int,
        band_name: str,
        output_path: Path,
        global_stats: Dict,
        profile: Dict,
    ):
        """Extrait et normalise une bande"""
        min_val = global_stats[band_name]["min"]
        max_val = global_stats[band_name]["max"]

        with rasterio.open(output_path, "w", **profile) as dst:
            for ji, window in src.block_windows(1):
                block = src.read(band_idx, window=window).astype(np.float32)

                valid_mask = (block > 0) & (block < 65535)
                normalized_block = np.zeros_like(block, dtype=np.uint16)

                if max_val > min_val:
                    normalized_values = (
                        (block[valid_mask] - min_val) / (max_val - min_val) * 65535
                    ).astype(np.uint16)
                    normalized_block[valid_mask] = normalized_values

                dst.write(normalized_block, 1, window=window)

                del block, normalized_block
                if "normalized_values" in locals():
                    del normalized_values
                gc.collect()

    def _merge_band_files(
        self, band_files: List[str], output_path: Path, band_name: str
    ):
        """Fusionne plusieurs fichiers de bande"""
        src_files = [rasterio.open(f) for f in band_files]

        try:
            mosaic, out_trans = merge(src_files)

            out_profile = src_files[0].profile.copy()
            out_profile.update(
                {
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": out_trans,
                    "compress": "lzw",
                    "BIGTIFF": "YES",
                }
            )

            with rasterio.open(output_path, "w", **out_profile) as dst:
                dst.write(mosaic[0], 1)

        finally:
            for src in src_files:
                src.close()
            del mosaic
            gc.collect()

    def _calculate_indices(self, merged_bands: Dict[str, str]) -> Dict[str, str]:
        """Calcule tous les indices de végétation"""
        red_path = merged_bands["red"]
        green_path = merged_bands["green"]
        blue_path = merged_bands["blue"]
        nir_path = merged_bands["nir"]

        # Fichiers de sortie
        indices_paths = {
            "NDVI": self.output_dir / "NDVI.tif",
            "SAVI": self.output_dir / "SAVI.tif",
            "EVI": self.output_dir / "EVI.tif",
            "AVI": self.output_dir / "AVI.tif",
            "BI_NIR": self.output_dir / "BI_NIR.tif",
            "RATIO": self.output_dir / "RATIO.tif",
            "BSI": self.output_dir / "BSI.tif",
            "composite": self.output_dir / "vegetation_indices_composite.tif",
        }

        with rasterio.open(red_path) as red_src:
            profile = red_src.profile.copy()
            profile.update({"dtype": "float32", "compress": "lzw", "BIGTIFF": "YES"})

            # Profil pour le composite (7 bandes)
            composite_profile = profile.copy()
            composite_profile.update({"count": 7})

            # Ouvrir tous les fichiers de sortie
            with rasterio.open(green_path) as green_src, rasterio.open(
                blue_path
            ) as blue_src, rasterio.open(nir_path) as nir_src:

                output_files = {}
                for name, path in indices_paths.items():
                    if name == "composite":
                        output_files[name] = rasterio.open(
                            path, "w", **composite_profile
                        )
                    else:
                        output_files[name] = rasterio.open(path, "w", **profile)

                try:
                    # Traitement par blocs
                    for ji, window in red_src.block_windows(1):
                        # Lire les blocs normalisés [0-1]
                        red_block = (
                            red_src.read(1, window=window).astype(np.float32) / 65535.0
                        )
                        green_block = (
                            green_src.read(1, window=window).astype(np.float32)
                            / 65535.0
                        )
                        blue_block = (
                            blue_src.read(1, window=window).astype(np.float32) / 65535.0
                        )
                        nir_block = (
                            nir_src.read(1, window=window).astype(np.float32) / 65535.0
                        )

                        # Calculer tous les indices
                        indices_blocks = self._compute_indices_block(
                            red_block, green_block, blue_block, nir_block
                        )

                        # Écrire tous les blocs
                        for i, (name, block) in enumerate(indices_blocks.items()):
                            if name == "composite":
                                continue
                            output_files[name].write(block, 1, window=window)
                            output_files["composite"].write(block, i + 1, window=window)

                        # Libérer la mémoire
                        del red_block, green_block, blue_block, nir_block
                        for block in indices_blocks.values():
                            del block
                        gc.collect()

                finally:
                    # Fermer tous les fichiers
                    for f in output_files.values():
                        f.close()

        return {name: str(path) for name, path in indices_paths.items()}

    def _compute_indices_block(
        self, red: np.ndarray, green: np.ndarray, blue: np.ndarray, nir: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """Calcule tous les indices pour un bloc donné"""
        indices = {}

        # NDVI: (NIR - Red) / (NIR + Red)
        denom_ndvi = nir + red
        ndvi = np.zeros_like(red, dtype=np.float32)
        mask_ndvi = denom_ndvi != 0
        ndvi[mask_ndvi] = (nir[mask_ndvi] - red[mask_ndvi]) / denom_ndvi[mask_ndvi]
        indices["NDVI"] = ndvi

        # SAVI: (1 + L) * (NIR - Red) / (NIR + Red + L), L = 0.5
        L = 0.5
        denom_savi = nir + red + L
        savi = np.zeros_like(red, dtype=np.float32)
        mask_savi = denom_savi != 0
        savi[mask_savi] = (
            (1.0 + L) * (nir[mask_savi] - red[mask_savi]) / denom_savi[mask_savi]
        )
        indices["SAVI"] = savi

        # EVI: G * ((NIR – R) / (NIR + C1 * R – C2 * B + L))
        G, C1, C2, L_evi = 2.5, 6.0, 7.5, 1.0
        denom_evi = nir + C1 * red - C2 * blue + L_evi
        evi = np.zeros_like(red, dtype=np.float32)
        mask_evi = denom_evi != 0
        evi[mask_evi] = G * (nir[mask_evi] - red[mask_evi]) / denom_evi[mask_evi]
        indices["EVI"] = evi

        # AVI: [NIR * (1-Red) * (NIR-Red)]^(1/3)
        avi_component = nir * (1 - red) * (nir - red)
        avi = np.zeros_like(red, dtype=np.float32)
        mask_avi_pos = avi_component >= 0
        mask_avi_neg = avi_component < 0
        avi[mask_avi_pos] = np.power(avi_component[mask_avi_pos], 1 / 3)
        avi[mask_avi_neg] = -np.power(np.abs(avi_component[mask_avi_neg]), 1 / 3)
        indices["AVI"] = avi

        # BI_NIR: (R + G + B + NIR) / 4
        indices["BI_NIR"] = (red + green + blue + nir) / 4.0

        # Ratio: NIR / (R + G + B)
        denom_ratio = red + green + blue
        ratio = np.zeros_like(red, dtype=np.float32)
        mask_ratio = denom_ratio != 0
        ratio[mask_ratio] = nir[mask_ratio] / denom_ratio[mask_ratio]
        indices["RATIO"] = ratio

        # BSI: ((R+G)+(NIR+B))/((R+G)−(NIR+B))
        numerator_bsi = (red + green) + (nir + blue)
        denominator_bsi = (red + green) - (nir + blue)
        bsi = np.zeros_like(red, dtype=np.float32)
        mask_bsi = denominator_bsi != 0
        bsi[mask_bsi] = numerator_bsi[mask_bsi] / denominator_bsi[mask_bsi]
        indices["BSI"] = bsi

        return indices

    def get_indices_statistics(self, indices_paths: Dict[str, str]) -> Dict[str, Dict]:
        """Calcule les statistiques des indices de végétation"""
        print("📈 Calcul des statistiques des indices")

        stats = {}

        for index_name, file_path in indices_paths.items():
            if index_name == "composite" or not os.path.exists(file_path):
                continue

            with rasterio.open(file_path) as src:
                data = src.read(1, masked=True)

                stats[index_name] = {
                    "min": float(np.min(data)),
                    "max": float(np.max(data)),
                    "mean": float(np.mean(data)),
                    "std": float(np.std(data)),
                    "percentile_1": float(np.percentile(data, 1)),
                    "percentile_5": float(np.percentile(data, 5)),
                    "percentile_25": float(np.percentile(data, 25)),
                    "percentile_75": float(np.percentile(data, 75)),
                    "percentile_95": float(np.percentile(data, 95)),
                    "percentile_99": float(np.percentile(data, 99)),
                }

        return stats
