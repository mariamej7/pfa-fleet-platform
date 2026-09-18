from pathlib import Path
from time import perf_counter

from pyspark.sql import functions as F

from spark_processing import (
    create_spark_session,
    load_telemetry_spark,
    prepare_telemetry_spark,
)


SOURCE = Path(
    r"D:\PFA\pfa-fleet-platform\data\uploads\199dea18e257444abc7f0e848806cc07.csv"
)


def main():

    spark = create_spark_session(
        "PFA-Scalability-Test"
    )

    try:

        # ====================================================
        # 1. LECTURE DU DATASET ORITECH
        # ====================================================

        print(
            "\n===== DATASET ORITECH ====="
        )

        df = load_telemetry_spark(
            SOURCE,
            spark,
        )

        original_count = (
            df.count()
        )

        print(
            "Lignes originales :",
            original_count,
        )

        # ====================================================
        # 2. CREATION D'UN VOLUME 10 FOIS PLUS GRAND
        # ====================================================

        copies = (
            spark
            .range(10)
            .withColumnRenamed(
                "id",
                "copy_id",
            )
        )

        large_df = (
            df
            .crossJoin(
                copies
            )
            .withColumn(
                "deviceId",
                (
                    F.col("deviceId")
                    +
                    F.col("copy_id") * 1000
                ),
            )
            .drop(
                "copy_id"
            )
        )

        large_count = (
            large_df.count()
        )

        vehicle_count = (
            large_df
            .select(
                "deviceId"
            )
            .distinct()
            .count()
        )

        print(
            "\n===== TEST DE MONTEE EN CHARGE ====="
        )

        print(
            "Lignes :",
            large_count,
        )

        print(
            "Vehicules :",
            vehicle_count,
        )

        # ====================================================
        # 3. PREPARATION AVEC SPARK
        # ====================================================

        print(
            "\nPreparation Spark en cours..."
        )

        start = perf_counter()

        _, report = (
            prepare_telemetry_spark(
                large_df
            )
        )

        duration = (
            perf_counter()
            - start
        )

        # ====================================================
        # 4. RESULTATS
        # ====================================================

        print(
            "\n===== RESULTATS SPARK ====="
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
            "Temps de traitement :",
            round(
                duration,
                2,
            ),
            "secondes",
        )

        print(
            "\nTEST DE MONTEE EN CHARGE SPARK OK"
        )

    finally:

        spark.stop()


if __name__ == "__main__":
    main()