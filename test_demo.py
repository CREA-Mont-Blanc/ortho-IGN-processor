"""
Test and demonstration script for the orthophotographic processor
"""

import os
import tempfile
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from ortho_processor.vegetation_indices import VegetationIndicesCalculator
from ortho_processor.thresholding import VegetationThresholder


def create_test_rgbnir_image(output_path: str, width: int = 1000, height: int = 1000):
    """
    Creates a test RGBNIR image with varied patterns

    Args:
        output_path: Output path
        width: Image width
        height: Image height
    """
    print(f"Creating test image: {output_path}")

    # Geographic transformation (example around the Alps region)
    transform = from_bounds(900000, 6400000, 902000, 6402000, width, height)

    # Create synthetic data
    np.random.seed(42)  # For reproducibility

    # Create different zones
    nir = np.zeros((height, width), dtype=np.uint16)
    red = np.zeros((height, width), dtype=np.uint16)
    green = np.zeros((height, width), dtype=np.uint16)
    blue = np.zeros((height, width), dtype=np.uint16)

    # Zone 1: Dense vegetation (upper left corner)
    h1, w1 = height // 3, width // 3
    nir[:h1, :w1] = np.random.randint(20000, 35000, (h1, w1))  # High NIR
    red[:h1, :w1] = np.random.randint(8000, 15000, (h1, w1))  # Moderate red
    green[:h1, :w1] = np.random.randint(12000, 20000, (h1, w1))  # High green
    blue[:h1, :w1] = np.random.randint(5000, 12000, (h1, w1))  # Low blue

    # Zone 2: Bare soil/rocky (upper right corner)
    nir[:h1, w1 : 2 * w1] = np.random.randint(15000, 25000, (h1, w1))
    red[:h1, w1 : 2 * w1] = np.random.randint(18000, 28000, (h1, w1))
    green[:h1, w1 : 2 * w1] = np.random.randint(16000, 26000, (h1, w1))
    blue[:h1, w1 : 2 * w1] = np.random.randint(14000, 24000, (h1, w1))

    # Zone 3: Water (lower left corner)
    h2 = 2 * height // 3
    nir[h2:, :w1] = np.random.randint(2000, 8000, (height - h2, w1))
    red[h2:, :w1] = np.random.randint(3000, 9000, (height - h2, w1))
    green[h2:, :w1] = np.random.randint(4000, 10000, (height - h2, w1))
    blue[h2:, :w1] = np.random.randint(5000, 12000, (height - h2, w1))

    # Zone 4: Sparse vegetation (rest of the image)
    mask = np.ones((height, width), dtype=bool)
    mask[:h1, :w1] = False
    mask[:h1, w1 : 2 * w1] = False
    mask[h2:, :w1] = False

    nir[mask] = np.random.randint(12000, 22000, np.sum(mask))
    red[mask] = np.random.randint(10000, 18000, np.sum(mask))
    green[mask] = np.random.randint(11000, 19000, np.sum(mask))
    blue[mask] = np.random.randint(7000, 15000, np.sum(mask))

    # File metadata
    profile = {
        "driver": "GTiff",
        "dtype": "uint16",
        "nodata": 0,
        "width": width,
        "height": height,
        "count": 4,
        "crs": "EPSG:2154",  # Lambert 93
        "transform": transform,
        "compress": "lzw",
    }

    # Write the file
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(nir, 1)  # Band 1: NIR
        dst.write(red, 2)  # Band 2: Red
        dst.write(green, 3)  # Band 3: Green
        dst.write(blue, 4)  # Band 4: Blue

    print(f"   Image created: {width}x{height} pixels, 4 bands")


def test_vegetation_indices():
    """
    Test vegetation indices calculation
    """
    print("\nTEST VEGETATION INDICES CALCULATION")
    print("=" * 50)

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test image
        test_image = os.path.join(temp_dir, "test_rgbnir.tif")
        create_test_rgbnir_image(test_image, 500, 500)

        # Indices calculator
        output_dir = os.path.join(temp_dir, "indices")
        calculator = VegetationIndicesCalculator(output_dir)

        # Calculate indices
        print("\nCalculating vegetation indices...")
        indices_paths = calculator.process_files([test_image])

        # Display results
        print("\nCalculated indices:")
        for name, path in indices_paths.items():
            if name != "composite" and os.path.exists(path):
                with rasterio.open(path) as src:
                    data = src.read(1, masked=True)
                    print(
                        f"   {name:8s}: min={np.min(data):.3f}, max={np.max(data):.3f}, "
                        f"mean={np.mean(data):.3f}"
                    )

        # Calculate detailed statistics
        print("\nCalculating detailed statistics...")
        stats = calculator.get_indices_statistics(indices_paths)

        return indices_paths, stats


def test_thematic_mapping(indices_paths: dict, stats: dict):
    """
    Test thematic mapping
    """
    print("\nTEST THEMATIC MAPPING")
    print("=" * 45)

    # Create a temporary directory for maps
    with tempfile.TemporaryDirectory() as temp_dir:
        # Thresholder
        thresholder = VegetationThresholder(temp_dir)

        # Display statistics
        thresholder.display_statistics(stats)

        # Predefined test thresholds
        test_thresholds = {
            "dense_vegetation": [
                {"index": "NDVI", "operator": ">", "threshold": 0.4},
                {"index": "SAVI", "operator": ">", "threshold": 0.3},
            ],
            "bare_soil": [
                {"index": "BSI", "operator": ">", "threshold": 0.0},
                {"index": "NDVI", "operator": "<", "threshold": 0.3},
            ],
            "water": [
                {"index": "RATIO", "operator": "<", "threshold": 0.5},
                {"index": "BI_NIR", "operator": "<", "threshold": 0.3},
            ],
        }

        print("\nApplying test thresholds...")
        for zone_name, conditions in test_thresholds.items():
            print(f"   {zone_name}:")
            for condition in conditions:
                print(
                    f"     {condition['index']} {condition['operator']} {condition['threshold']}"
                )

        # Create thematic maps
        thematic_maps = thresholder.create_thematic_maps(indices_paths, test_thresholds)

        # Calculate zone statistics
        zone_stats = thresholder.calculate_zone_statistics(thematic_maps)

        # Create report
        report_path = thresholder.create_summary_report(zone_stats, test_thresholds)

        print(f"\nTest report created: {report_path}")

        # Read and display report
        if os.path.exists(report_path):
            print("\nREPORT CONTENT:")
            print("-" * 25)
            with open(report_path, "r", encoding="utf-8") as f:
                print(f.read())


def demo_interactive_workflow():
    """
    Demonstration of the interactive workflow (without user interface)
    """
    print("\nCOMPLETE WORKFLOW DEMONSTRATION")
    print("=" * 40)

    try:
        # Test vegetation indices
        indices_paths, stats = test_vegetation_indices()

        # Test thematic mapping
        test_thematic_mapping(indices_paths, stats)

        print("\nDEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("All modules are working correctly")

    except Exception as e:
        print(f"\nERROR DURING DEMONSTRATION: {e}")
        import traceback

        traceback.print_exc()


def show_available_indices():
    """
    Display available indices and their formulas
    """
    print("\nAVAILABLE VEGETATION INDICES")
    print("=" * 40)

    indices_info = {
        "NDVI": {
            "name": "Normalized Difference Vegetation Index",
            "formula": "(NIR - Red) / (NIR + Red)",
            "range": "[-1, 1]",
            "usage": "General vegetation detection",
        },
        "SAVI": {
            "name": "Soil Adjusted Vegetation Index",
            "formula": "(1 + L) × (NIR - Red) / (NIR + Red + L)",
            "range": "[-1.5, 1.5]",
            "usage": "Vegetation with soil correction (L=0.5)",
        },
        "EVI": {
            "name": "Enhanced Vegetation Index",
            "formula": "G × (NIR - Red) / (NIR + C1×Red - C2×Blue + L)",
            "range": "[-1, 1]",
            "usage": "Dense vegetation, less saturated than NDVI",
        },
        "AVI": {
            "name": "Advanced Vegetation Index",
            "formula": "[NIR × (1-Red) × (NIR-Red)]^(1/3)",
            "range": "[-2, 2]",
            "usage": "Advanced vegetation with cube root",
        },
        "BI_NIR": {
            "name": "Brightness Index with NIR",
            "formula": "(Red + Green + Blue + NIR) / 4",
            "range": "[0, 1]",
            "usage": "General brightness index",
        },
        "RATIO": {
            "name": "NIR/RGB Ratio",
            "formula": "NIR / (Red + Green + Blue)",
            "range": "[0, ∞]",
            "usage": "Simple NIR to visible ratio",
        },
        "BSI": {
            "name": "Bare Soil Index",
            "formula": "((Red+Green)+(NIR+Blue)) / ((Red+Green)-(NIR+Blue))",
            "range": "[-∞, ∞]",
            "usage": "Bare soil detection",
        },
    }

    for code, info in indices_info.items():
        print(f"\n{code} - {info['name']}")
        print(f"   Formula: {info['formula']}")
        print(f"   Range:   {info['range']}")
        print(f"   Usage:   {info['usage']}")


if __name__ == "__main__":
    print("ORTHOPHOTOGRAPHIC PROCESSOR TEST AND DEMONSTRATION")
    print("=" * 65)

    # Display available indices
    show_available_indices()

    # Launch demonstration
    demo_interactive_workflow()
