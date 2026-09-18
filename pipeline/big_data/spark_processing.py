from pathlib import Path
from typing import Union

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


# ============================================================
# COLONNES OBLIGATOIRES
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
# SESSION SPARK
# ============================================================

def create_spark_session(
    app_name: str = "PFA-Fleet-Spark",
) -> SparkSession:
    """
    Crée une session Spark locale pour le PFA.
    """

    spark = (
        SparkSession.builder
        .master("local[*]")
        .appName(app_name)
        .config(
            "spark.sql.shuffle.partitions",
            "4",
        )
        .config(
            "spark.sql.session.timeZone",
            "UTC",
        )
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel(
        "WARN"
    )

    return spark


# ============================================================
# LECTURE CSV / PARQUET
# ============================================================

def load_telemetry_spark(
    file_path: Union[str, Path],
    spark: SparkSession,
) -> DataFrame:
    """
    Charge un fichier CSV ou Parquet avec Spark.
    """

    file_path = Path(
        file_path
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {file_path}"
        )

    extension = (
        file_path.suffix.lower()
    )

    if extension == ".csv":

        df = (
            spark.read
            .option(
                "header",
                True,
            )
            .option(
                "inferSchema",
                True,
            )
            .csv(
                str(file_path)
            )
        )

    elif extension == ".parquet":

        df = (
            spark.read
            .parquet(
                str(file_path)
            )
        )

    else:

        raise ValueError(
            (
                "Format non supporté. "
                "Utiliser CSV ou Parquet."
            )
        )

    return df


# ============================================================
# VALIDATION DES COLONNES
# ============================================================

def validate_required_columns(
    df: DataFrame,
) -> None:
    """
    Vérifie les colonnes nécessaires au pipeline.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            (
                "Colonnes obligatoires "
                f"manquantes : {missing_columns}"
            )
        )


# ============================================================
# PREPARATION SPARK
# ============================================================

def prepare_telemetry_spark(
    df_raw: DataFrame,
) -> tuple[DataFrame, dict]:
    """
    Reproduit avec Spark les principales étapes
    de préparation du pipeline Pandas actuel.
    """

    validate_required_columns(
        df_raw
    )

    # --------------------------------------------------------
    # 1. Nombre de lignes brutes
    # --------------------------------------------------------

    raw_count = (
        df_raw.count()
    )

    # --------------------------------------------------------
    # 2. Conversion de fixTime
    #
    # try_to_timestamp joue ici le même rôle
    # que errors="coerce" côté Pandas :
    # une date invalide devient NULL.
    # --------------------------------------------------------

    df = (
        df_raw
        .withColumn(
            "fixTime",
            F.try_to_timestamp(
                F.col("fixTime")
            ),
        )
    )

    invalid_dates_count = (
        df
        .filter(
            F.col("fixTime").isNull()
        )
        .count()
    )

    # --------------------------------------------------------
    # 3. Suppression des doublons exacts
    # --------------------------------------------------------

    df = (
        df
        .dropDuplicates()
    )

    prepared_count = (
        df.count()
    )

    duplicate_count = (
        raw_count
        - prepared_count
    )

    # --------------------------------------------------------
    # 4. Fenêtre temporelle par véhicule
    #
    # Equivalent Spark de :
    # groupby("deviceId") + shift/diff
    # --------------------------------------------------------

    vehicle_window = (
        Window
        .partitionBy(
            "deviceId"
        )
        .orderBy(
            "fixTime"
        )
    )

    # --------------------------------------------------------
    # 5. Mesure précédente
    # --------------------------------------------------------

    df = (
        df
        .withColumn(
            "prev_time",
            F.lag(
                "fixTime"
            ).over(
                vehicle_window
            ),
        )
        .withColumn(
            "prev_fuel",
            F.lag(
                "fuelLevel"
            ).over(
                vehicle_window
            ),
        )
        .withColumn(
            "prev_odometer",
            F.lag(
                "odometer"
            ).over(
                vehicle_window
            ),
        )
    )

    # --------------------------------------------------------
    # 6. Temps entre deux mesures
    # --------------------------------------------------------

    df = (
        df
        .withColumn(
            "delta_time_sec",
            (
                F.col("fixTime").cast("long")
                -
                F.col("prev_time").cast("long")
            ).cast("double"),
        )
        .withColumn(
            "delta_time_min",
            (
                F.col("delta_time_sec")
                / F.lit(60.0)
            ),
        )
        .withColumn(
            "delta_time_hours",
            (
                F.col("delta_time_sec")
                / F.lit(3600.0)
            ),
        )
    )

    # --------------------------------------------------------
    # 7. Conversion vitesse
    #
    # Données Oritech :
    # speed est exprimée en noeuds.
    #
    # 1 knot = 1.852 km/h
    # --------------------------------------------------------

    df = (
        df
        .withColumn(
            "speed_kmh",
            (
                F.col("speed")
                * F.lit(1.852)
            ),
        )
    )

    # --------------------------------------------------------
    # 8. Variation du carburant
    # --------------------------------------------------------

    df = (
        df
        .withColumn(
            "delta_fuel",
            (
                F.col("fuelLevel")
                -
                F.col("prev_fuel")
            ),
        )
    )

    # --------------------------------------------------------
    # 9. Variation odomètre
    # --------------------------------------------------------

    df = (
        df
        .withColumn(
            "delta_odometer_m",
            (
                F.col("odometer")
                -
                F.col("prev_odometer")
            ),
        )
    )

    # --------------------------------------------------------
    # 10. Contrôle qualité fuelLevel
    #
    # On considère incohérente une transition si :
    # - la valeur actuelle est hors [0, 100]
    # OU
    # - la valeur précédente est hors [0, 100]
    # --------------------------------------------------------

    current_fuel_out_of_range = (
        (
            F.col("fuelLevel") < 0
        )
        |
        (
            F.col("fuelLevel") > 100
        )
    )

    previous_fuel_out_of_range = (
        (
            F.col("prev_fuel") < 0
        )
        |
        (
            F.col("prev_fuel") > 100
        )
    )

    df = (
        df
        .withColumn(
            "flag_incoherence_fuel",
            (
                F.coalesce(
                    current_fuel_out_of_range,
                    F.lit(False),
                )
                |
                F.coalesce(
                    previous_fuel_out_of_range,
                    F.lit(False),
                )
            ),
        )
    )

    # --------------------------------------------------------
    # 11. Colonnes finales
    #
    # On retire seulement les colonnes techniques temporaires
    # prev_time et prev_odometer.
    # prev_fuel reste nécessaire au pipeline.
    # --------------------------------------------------------

    df = (
        df
        .drop(
            "prev_time",
            "prev_odometer",
        )
    )

    # --------------------------------------------------------
    # 12. Contrôles
    # --------------------------------------------------------

    vehicle_count = (
        df
        .select(
            "deviceId"
        )
        .distinct()
        .count()
    )

    fuel_out_of_range_count = (
        df
        .filter(
            (
                F.col("fuelLevel") < 0
            )
            |
            (
                F.col("fuelLevel") > 100
            )
        )
        .count()
    )

    incoherent_transition_count = (
        df
        .filter(
            F.col(
                "flag_incoherence_fuel"
            )
        )
        .count()
    )

    period = (
        df
        .agg(
            F.min(
                "fixTime"
            ).alias(
                "date_min"
            ),
            F.max(
                "fixTime"
            ).alias(
                "date_max"
            ),
        )
        .first()
    )

    report = {
        "nombre_lignes_brutes":
            int(raw_count),

        "nombre_doublons":
            int(duplicate_count),

        "nombre_lignes_preparees":
            int(prepared_count),

        "nombre_dates_invalides":
            int(invalid_dates_count),

        "nombre_vehicules":
            int(vehicle_count),

        "nombre_fuel_hors_plage":
            int(
                fuel_out_of_range_count
            ),

        "nombre_transitions_incoherentes":
            int(
                incoherent_transition_count
            ),

        "date_min":
            period["date_min"],

        "date_max":
            period["date_max"],
    }

    return df, report


# ============================================================
# TEST SUR LES DONNEES ORITECH
# ============================================================

if __name__ == "__main__":

    DATASET = Path(
        r"D:\PFA\pfa-fleet-platform\data\uploads\199dea18e257444abc7f0e848806cc07.csv"
    )

    spark = (
        create_spark_session()
    )

    try:

        print(
            "\n===== 1. LECTURE SPARK ====="
        )

        df_raw = (
            load_telemetry_spark(
                DATASET,
                spark,
            )
        )

        print(
            "\n===== 2. PREPARATION SPARK ====="
        )

        df_prepared, report = (
            prepare_telemetry_spark(
                df_raw
            )
        )

        print(
            "\n===== RESULTATS ====="
        )

        print(
            "Lignes brutes :",
            report[
                "nombre_lignes_brutes"
            ],
        )

        print(
            "Doublons exacts :",
            report[
                "nombre_doublons"
            ],
        )

        print(
            "Lignes preparees :",
            report[
                "nombre_lignes_preparees"
            ],
        )

        print(
            "Dates invalides :",
            report[
                "nombre_dates_invalides"
            ],
        )

        print(
            "Vehicules :",
            report[
                "nombre_vehicules"
            ],
        )

        print(
            "Fuel hors plage :",
            report[
                "nombre_fuel_hors_plage"
            ],
        )

        print(
            "Transitions incoherentes :",
            report[
                "nombre_transitions_incoherentes"
            ],
        )

        print(
            "Debut :",
            report[
                "date_min"
            ],
        )

        print(
            "Fin :",
            report[
                "date_max"
            ],
        )

        print(
            "Nombre de colonnes :",
            len(
                df_prepared.columns
            ),
        )

        print(
            "\nColonnes preparees :"
        )

        print(
            df_prepared.columns
        )

        print(
            "\nTEST PREPARATION SPARK OK"
        )

    finally:

        spark.stop()