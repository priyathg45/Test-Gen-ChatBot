"""Utility to synthesize a larger aluminum products dataset and preprocess it.

Usage
-----
python -m src.data.generate_dataset --target-size 1000 --seed 42

Outputs
-------
- data/aluminum_products_1000.csv (raw synthetic data)
- data/aluminum_products_1000_processed.csv (cleaned + combined_text)
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import List

import pandas as pd

from src.data.preprocessor import DataPreprocessor

# Reusable pools for light product variation
NAME_QUALIFIERS = [
    "Premium",
    "Industrial",
    "Lightweight",
    "Heat-Treated",
    "Corrosion-Guard",
    "Precision",
    "High-Ductility",
    "Anodized",
    "Mill Finish",
    "Structural",
]

DESCRIPTION_TRAITS = [
    "optimized for tight tolerance assemblies",
    "suited for high-vibration environments",
    "tested for extended fatigue life",
    "with enhanced corrosion mitigation",
    "balanced for stiffness and machinability",
    "ready for marine and coastal exposure",
    "with improved surface finish for coatings",
    "validated for aerospace-grade QA checks",
    "supports automated fabrication lines",
    "ideal for lightweight structural frames",
]

SPEC_SUFFIXES = [
    "Tolerance: ±0.2mm",
    "Heat treatment: T6 stabilized",
    "Surface finish: Ra 0.8µm",
    "Ultrasonic inspected",
    "Certification: EN 485 / ASTM B209",
    "Grain direction: longitudinal",
    "Coating ready",
    "Weldable with 4043/5356 filler",
    "Recyclability: >95%",
]

MANUFACTURERS = [
    "AluTech",
    "OceanAlloys",
    "SkyMetal",
    "BuildAluminum",
    "AeroAlloys",
    "RoofMetal",
    "ExtrudeMasters",
    "MotorAlloys",
    "WeldTech",
    "IndustrialMetal",
    "AdvancedAero",
    "PackAluminum",
    "MarineGrade",
    "CargoAluminum",
    "FastenerAlloy",
    "StructuralMetal",
    "HeavyMarine",
    "AeroFasteners",
    "CanMaker",
    "ArchMetal",
    "PrimeMetals",
    "NextGen Alloy",
    "EuroAlu",
    "Pacific Metals",
    "GlobalSmelt",
]


def load_base_dataset(base_path: Path) -> pd.DataFrame:
    if not base_path.exists():
        raise FileNotFoundError(f"Base dataset not found at {base_path}")
    return pd.read_csv(base_path)


def _bounded_int(value: float, low: int, high: int) -> int:
    return max(low, min(int(round(value)), high))


def _variant_from_row(row: pd.Series, new_id: int, rng: random.Random) -> dict:
    price = float(row.get("price", 0))
    # Price variation within ±18%
    price_multiplier = rng.uniform(0.82, 1.18)
    new_price = round(price * price_multiplier, 2)

    stock = row.get("stock_level", 0)
    try:
        stock = int(stock)
    except Exception:
        stock = 0
    stock_variation = rng.randint(-80, 120)
    new_stock = _bounded_int(stock + stock_variation, 0, 5000)

    base_name = str(row.get("product_name", "Aluminum Product"))
    qualifier = rng.choice(NAME_QUALIFIERS)
    name_variant = f"{base_name} {qualifier}"

    base_desc = str(row.get("description", ""))
    desc_trait = rng.choice(DESCRIPTION_TRAITS)
    description = f"{base_desc}; {desc_trait}"

    specs = str(row.get("specifications", ""))
    spec_suffix = rng.choice(SPEC_SUFFIXES)
    specifications = f"{specs}; {spec_suffix}"

    manufacturer = rng.choice(MANUFACTURERS)

    applications = str(row.get("applications", ""))
    category = str(row.get("category", "Industrial"))

    return {
        "product_id": new_id,
        "product_name": name_variant,
        "category": category,
        "description": description,
        "price": new_price,
        "specifications": specifications,
        "applications": applications,
        "manufacturer": manufacturer,
        "stock_level": new_stock,
    }


def generate_dataset(base_df: pd.DataFrame, target_size: int, seed: int) -> pd.DataFrame:
    rng = random.Random(seed)
    records: List[dict] = []
    base_len = len(base_df)
    if base_len == 0:
        raise ValueError("Base dataset is empty; cannot generate variants.")

    for i in range(target_size):
        base_row = base_df.iloc[i % base_len]
        new_id = i + 1  # ensure continuous IDs
        records.append(_variant_from_row(base_row, new_id, rng))

    df = pd.DataFrame(records)
    return df


def preprocess_and_save(df: pd.DataFrame, processed_path: Path) -> pd.DataFrame:
    preprocessor = DataPreprocessor(df)
    preprocessor.preprocess_all()
    processed_df = preprocessor.get_processed_data()
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    processed_df.to_csv(processed_path, index=False)
    return processed_df


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic aluminum products dataset.")
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path("data/aluminum_products.csv"),
        help="Base CSV to seed variants.",
    )
    parser.add_argument(
        "--target-size",
        type=int,
        default=4000,
        help="Number of records to generate (default: 4000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Directory to write generated files (aluminum_products.csv).",
    )
    args = parser.parse_args()

    base_df = load_base_dataset(args.base_path)
    generated = generate_dataset(base_df, args.target_size, args.seed)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    gen_path = args.output_dir / "aluminum_products.csv"
    generated.to_csv(gen_path, index=False)

    # Also write a preprocessed version if you want to inspect it, but the app
    # will preprocess again at startup using DataPreprocessor.
    processed_path = args.output_dir / "aluminum_products_preprocessed.csv"
    processed_df = preprocess_and_save(generated, processed_path)

    print(f"Generated dataset saved to: {gen_path} ({len(generated)} rows)")
    print(f"Preprocessed dataset saved to: {processed_path} ({len(processed_df)} rows)")
    print("Columns:", processed_df.columns.tolist())


if __name__ == "__main__":
    main()
