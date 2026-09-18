import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CHEMINS
# ============================================================

PROJECT_ROOT = Path(
    r"D:\PFA\pfa-fleet-platform"
)

PIPELINE_DIR = (
    PROJECT_ROOT / "pipeline"
)

if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(PIPELINE_DIR),
    )


DATASET = (
    PROJECT_ROOT
    / "data"
    / "uploads"
    / "199dea18e257444abc7f0e848806cc07.csv"
)


# ============================================================
# IMPORTS PIPELINE
# ============================================================

from preprocessing.prepare_data import (
    prepare_fleet_data,
)

from analytics.compute_kpis import (
    compute_fleet_kpis,
)

from big_data.spark_processing import (
    create_spark_session,
    load_telemetry_spark,
    prepare_telemetry_spark,
)

from big_data.spark_kpis import (
    compute_fleet_kpis_spark,
)


# ============================================================
# OUTILS DE COMPARAISON
# ============================================================

def compare_numeric_column(
    pandas_df,
    spark_df,
    column,
    tolerance=1e-6,
):
    """
    Compare une colonne numérique
    véhicule par véhicule.
    """

    left = (
        pandas_df[
            [
                "deviceId",
                column,
            ]
        ]
        .copy()
    )

    right = (
        spark_df[
            [
                "deviceId",
                column,
            ]
        ]
        .copy()
    )

    comparison = left.merge(
        right,
        on="deviceId",
        how="outer",
        suffixes=(
            "_pandas",
            "_spark",
        ),
    )

    pandas_values = pd.to_numeric(
        comparison[
            f"{column}_pandas"
        ],
        errors="coerce",
    )

    spark_values = pd.to_numeric(
        comparison[
            f"{column}_spark"
        ],
        errors="coerce",
    )

    same_nan = (
        pandas_values.isna()
        &
        spark_values.isna()
    )

    close_values = np.isclose(
        pandas_values.fillna(0),
        spark_values.fillna(0),
        rtol=tolerance,
        atol=tolerance,
    )

    ok = bool(
        (
            same_nan
            |
            close_values
        ).all()
    )

    if ok:
        print(
            f"[OK] {column}"
        )

    else:
        print(
            f"[DIFFERENCE] {column}"
        )

        print(
            comparison.to_string(
                index=False
            )
        )

    return ok


# ============================================================
# TEST
# ============================================================

print()
print(
    "=============================================="
)
print(
    "TEST KPI SPARK VS PANDAS - ORITECH"
)
print(
    "=============================================="
)


# ============================================================
# 1. PANDAS
# ============================================================

print()
print(
    "1. Pipeline Pandas"
)

df_pandas, pandas_report = (
    prepare_fleet_data(
        DATASET
    )
)

pandas_kpis = (
    compute_fleet_kpis(
        df_pandas
    )
)

pandas_daily = (
    pandas_kpis[
        "kpi_daily"
    ]
)

pandas_vehicle = (
    pandas_kpis[
        "kpi_vehicle"
    ]
)

pandas_global = (
    pandas_kpis[
        "kpi_global"
    ]
)

print(
    "[OK] Lignes préparées :",
    len(df_pandas),
)

print(
    "[OK] KPI journaliers :",
    len(pandas_daily),
)

print(
    "[OK] Véhicules :",
    len(pandas_vehicle),
)


# ============================================================
# 2. SPARK
# ============================================================

print()
print(
    "2. Pipeline Spark"
)

spark = (
    create_spark_session(
        app_name=
            "PFA-Test-KPI-Spark-vs-Pandas"
    )
)


try:

    df_raw_spark = (
        load_telemetry_spark(
            DATASET,
            spark,
        )
    )

    (
        df_spark,
        spark_report,
    ) = (
        prepare_telemetry_spark(
            df_raw_spark
        )
    )

    spark_kpis = (
        compute_fleet_kpis_spark(
            df_spark
        )
    )

    spark_daily = (
        spark_kpis[
            "kpi_daily"
        ]
    )

    spark_vehicle = (
        spark_kpis[
            "kpi_vehicle"
        ]
    )

    spark_global = (
        spark_kpis[
            "kpi_global"
        ]
    )

    print(
        "[OK] Lignes préparées :",
        spark_report[
            "nombre_lignes_preparees"
        ],
    )

    print(
        "[OK] KPI journaliers :",
        len(
            spark_daily
        ),
    )

    print(
        "[OK] Véhicules :",
        len(
            spark_vehicle
        ),
    )


    # ========================================================
    # 3. CONTROLES GENERAUX
    # ========================================================

    print()
    print(
        "3. Comparaison générale"
    )

    problems = []

    if (
        len(df_pandas)
        ==
        spark_report[
            "nombre_lignes_preparees"
        ]
    ):
        print(
            "[OK] Même nombre de lignes préparées"
        )
    else:
        print(
            "[ERREUR] Nombre de lignes préparées différent"
        )
        problems.append(
            "prepared_rows"
        )

    if (
        len(pandas_daily)
        ==
        len(spark_daily)
    ):
        print(
            "[OK] Même nombre de KPI journaliers"
        )
    else:
        print(
            "[ERREUR] Nombre de KPI journaliers différent"
        )
        problems.append(
            "daily_rows"
        )

    if (
        len(pandas_vehicle)
        ==
        len(spark_vehicle)
    ):
        print(
            "[OK] Même nombre de véhicules"
        )
    else:
        print(
            "[ERREUR] Nombre de véhicules différent"
        )
        problems.append(
            "vehicle_rows"
        )


    # ========================================================
    # 4. KPI PAR VEHICULE
    # ========================================================

    print()
    print(
        "4. Comparaison KPI par véhicule"
    )

    numeric_columns = [
        "nombre_mesures",
        "jours_calendaires_periode",
        "jours_avec_donnees",
        "jours_actifs",
        "taux_couverture_jours_pct",
        "distance_km",
        "distance_moyenne_par_jour_actif_km",
        "vitesse_moyenne_mesures_kmh",
        "vitesse_moyenne_en_mouvement_kmh",
        "vitesse_max_kmh",
        "fuel_moyen_pct",
        "fuel_min_pct",
        "fuel_max_pct",
        "nb_incoherences_fuel",
        "pct_incoherences_fuel",
    ]

    for column in numeric_columns:

        ok = compare_numeric_column(
            pandas_vehicle,
            spark_vehicle,
            column,
        )

        if not ok:
            problems.append(
                column
            )


    # ========================================================
    # 5. KPI GLOBAUX
    # ========================================================

    print()
    print(
        "5. KPI globaux"
    )

    global_columns = [
        "nombre_vehicules",
        "nombre_total_mesures",
        "distance_totale_km",
        "nb_incoherences_fuel",
    ]

    for column in global_columns:

        pandas_value = (
            pandas_global[
                column
            ]
        )

        spark_value = (
            spark_global[
                column
            ]
        )

        if np.isclose(
            float(pandas_value),
            float(spark_value),
            rtol=1e-6,
            atol=1e-6,
        ):

            print(
                f"[OK] {column} : "
                f"{pandas_value}"
            )

        else:

            print(
                f"[ERREUR] {column}"
            )

            print(
                "    Pandas :",
                pandas_value,
            )

            print(
                "    Spark  :",
                spark_value,
            )

            problems.append(
                f"global_{column}"
            )


    # ========================================================
    # 6. RESULTAT FINAL
    # ========================================================

    print()
    print(
        "=============================================="
    )

    if not problems:

        print(
            "TEST KPI SPARK VS PANDAS : OK"
        )

    else:

        print(
            "TEST KPI SPARK VS PANDAS : DIFFERENCES"
        )

        print(
            "Points à vérifier :"
        )

        for problem in problems:
            print(
                "-",
                problem,
            )

    print(
        "=============================================="
    )


finally:

    spark.stop()