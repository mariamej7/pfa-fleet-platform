from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


# ============================================================
# COLONNES ATTENDUES
# ============================================================

REQUIRED_COLUMNS = [
    "deviceId",
    "fixTime",
    "latitude",
    "longitude",
    "speed",
    "fuelLevel",
    "odometer",
    "ignition",
]


# ============================================================
# CHARGEMENT DU DATASET
# ============================================================

def load_fleet_dataset(file_path: str) -> pd.DataFrame:
    """
    Charge un fichier télématique CSV ou Parquet
    et vérifie que les colonnes nécessaires sont présentes.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {path}"
        )

    extension = path.suffix.lower()

    if extension == ".csv":
        df = pd.read_csv(path)

    elif extension == ".parquet":
        df = pd.read_parquet(path)

    else:
        raise ValueError(
            "Format non supporté. "
            "Formats acceptés : CSV et Parquet."
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Dataset incompatible. "
            f"Colonnes manquantes : {missing_columns}"
        )

    return df


# ============================================================
# PREPARATION DES DONNEES
# ============================================================

def prepare_fleet_data(
    file_path: str,
) -> Tuple[pd.DataFrame, Dict]:
    """
    Prépare le dataset télématique pour les étapes
    suivantes du pipeline.

    Cette fonction :
    - charge le dataset ;
    - convertit fixTime en datetime ;
    - compte les dates invalides ;
    - compte et supprime les doublons exacts ;
    - trie les mesures par véhicule et par temps ;
    - calcule les écarts temporels ;
    - convertit speed de knots vers km/h ;
    - calcule delta_fuel ;
    - calcule prev_fuel ;
    - calcule delta_odometer_m ;
    - signale les incohérences fuelLevel.
    """

    # --------------------------------------------------------
    # 1. Chargement
    # --------------------------------------------------------

    df = load_fleet_dataset(file_path)

    nombre_lignes_brutes = len(df)

    # --------------------------------------------------------
    # 2. Conversion de fixTime
    # --------------------------------------------------------

    df["fixTime"] = pd.to_datetime(
        df["fixTime"],
        format="mixed",
        errors="coerce",
    )

    nombre_dates_invalides = int(
        df["fixTime"].isna().sum()
    )

    # --------------------------------------------------------
    # 3. Valeurs manquantes
    # --------------------------------------------------------

    valeurs_manquantes = {
        column: int(value)
        for column, value in (
            df[REQUIRED_COLUMNS]
            .isna()
            .sum()
            .items()
        )
    }

    # --------------------------------------------------------
    # 4. Doublons exacts
    # --------------------------------------------------------

    nombre_doublons = int(
        df.duplicated().sum()
    )

    # Même logique que dans le notebook
    df_time = (
        df
        .drop_duplicates()
        .copy()
    )

    # --------------------------------------------------------
    # 5. Tri par véhicule et par temps
    # --------------------------------------------------------

    df_time = (
        df_time
        .sort_values(
            by=[
                "deviceId",
                "fixTime",
            ]
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # 6. Temps entre deux mesures
    # --------------------------------------------------------

    df_time["delta_time_sec"] = (
        df_time
        .groupby("deviceId")["fixTime"]
        .diff()
        .dt.total_seconds()
    )

    df_time["delta_time_min"] = (
        df_time["delta_time_sec"] / 60
    )

    df_time["delta_time_hours"] = (
        df_time["delta_time_sec"] / 3600
    )

    # --------------------------------------------------------
    # 7. Conversion de speed
    # knots -> km/h
    # --------------------------------------------------------

    df_time["speed_kmh"] = (
        df_time["speed"] * 1.852
    )

    # --------------------------------------------------------
    # 8. Variation de carburant
    # --------------------------------------------------------

    df_time["delta_fuel"] = (
        df_time
        .groupby("deviceId")["fuelLevel"]
        .diff()
    )

    # --------------------------------------------------------
    # 9. Niveau de carburant précédent
    # --------------------------------------------------------

    df_time["prev_fuel"] = (
        df_time
        .groupby("deviceId")["fuelLevel"]
        .shift(1)
    )

    # --------------------------------------------------------
    # 10. Variation de l'odomètre
    # --------------------------------------------------------

    df_time["delta_odometer_m"] = (
        df_time
        .groupby("deviceId")["odometer"]
        .diff()
    )

    # --------------------------------------------------------
    # 11. Contrôle qualité fuelLevel
    # --------------------------------------------------------

    fuel_hors_plage = (
        (df_time["fuelLevel"] < 0)
        |
        (df_time["fuelLevel"] > 100)
    )

    prev_fuel_hors_plage = (
        (df_time["prev_fuel"] < 0)
        |
        (df_time["prev_fuel"] > 100)
    )

    df_time["flag_incoherence_fuel"] = (
        fuel_hors_plage
        |
        prev_fuel_hors_plage
    )

    # --------------------------------------------------------
    # 12. Rapport de préparation
    # --------------------------------------------------------

    nombre_lignes_preparees = len(df_time)

    debut_periode = df_time["fixTime"].min()
    fin_periode = df_time["fixTime"].max()

    rapport = {
        "nombre_lignes_brutes":
            nombre_lignes_brutes,

        "nombre_doublons_supprimes":
            nombre_doublons,

        "nombre_lignes_preparees":
            nombre_lignes_preparees,

        "lignes_supprimees_total":
            nombre_lignes_brutes
            - nombre_lignes_preparees,

        "nombre_vehicules":
            int(
                df_time["deviceId"].nunique()
            ),

        "nombre_dates_invalides":
            nombre_dates_invalides,

        "valeurs_manquantes":
            valeurs_manquantes,

        "nombre_fuel_hors_plage":
            int(fuel_hors_plage.sum()),

        "nombre_transitions_fuel_incoherentes":
            int(
                df_time[
                    "flag_incoherence_fuel"
                ].sum()
            ),

        "debut_periode":
            (
                debut_periode.isoformat()
                if pd.notna(debut_periode)
                else None
            ),

        "fin_periode":
            (
                fin_periode.isoformat()
                if pd.notna(fin_periode)
                else None
            ),
    }

    return df_time, rapport