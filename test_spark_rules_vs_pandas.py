import sys
from pathlib import Path

import numpy as np


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
# IMPORTS
# ============================================================

from preprocessing.prepare_data import (
    prepare_fleet_data,
)

from anomaly_detection.rule_detection import (
    detect_rule_events,
)

from big_data.spark_processing import (
    create_spark_session,
    load_telemetry_spark,
    prepare_telemetry_spark,
)

from big_data.spark_rule_detection import (
    detect_rule_events_spark,
)


# ============================================================
# OUTIL COMPARAISON
# ============================================================

def compare_number(
    label,
    pandas_value,
    spark_value,
    tolerance=1e-9,
):
    if pandas_value is None and spark_value is None:
        print(
            f"[OK] {label} : None"
        )
        return True

    if (
        pandas_value is None
        or spark_value is None
    ):
        print(
            f"[ERREUR] {label}"
        )
        print(
            "    Pandas :",
            pandas_value,
        )
        print(
            "    Spark  :",
            spark_value,
        )
        return False

    ok = np.isclose(
        float(pandas_value),
        float(spark_value),
        rtol=tolerance,
        atol=tolerance,
    )

    if ok:
        print(
            f"[OK] {label} : "
            f"{pandas_value}"
        )
    else:
        print(
            f"[ERREUR] {label}"
        )
        print(
            "    Pandas :",
            pandas_value,
        )
        print(
            "    Spark  :",
            spark_value,
        )

    return bool(ok)


# ============================================================
# DEBUT
# ============================================================

print()
print(
    "=============================================="
)
print(
    "TEST REGLES SPARK VS PANDAS - ORITECH"
)
print(
    "=============================================="
)


problems = []


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

pandas_rules = (
    detect_rule_events(
        df_pandas
    )
)

pandas_thresholds = (
    pandas_rules[
        "thresholds"
    ]
)

pandas_refuels = (
    pandas_rules[
        "refueling_episodes"
    ]
)

pandas_suspicious = (
    pandas_rules[
        "suspicious_events"
    ]
)

pandas_summary = (
    pandas_rules[
        "summary"
    ]
)

print(
    "[OK] Lignes préparées :",
    len(df_pandas),
)

print(
    "[OK] Episodes refuel :",
    len(pandas_refuels),
)

print(
    "[OK] Baisses suspectes :",
    len(pandas_suspicious),
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
            "PFA-Test-Rules-Spark-vs-Pandas"
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

    spark_rules = (
        detect_rule_events_spark(
            df_spark
        )
    )

    spark_thresholds = (
        spark_rules[
            "thresholds"
        ]
    )

    spark_refuels = (
        spark_rules[
            "refueling_episodes"
        ]
    )

    spark_suspicious = (
        spark_rules[
            "suspicious_events"
        ]
    )

    spark_summary = (
        spark_rules[
            "summary"
        ]
    )

    print(
        "[OK] Lignes préparées :",
        spark_report[
            "nombre_lignes_preparees"
        ],
    )

    print(
        "[OK] Episodes refuel :",
        len(
            spark_refuels
        ),
    )

    print(
        "[OK] Baisses suspectes :",
        len(
            spark_suspicious
        ),
    )


    # ========================================================
    # 3. SEUILS
    # ========================================================

    print()
    print(
        "3. Comparaison des seuils"
    )

    threshold_columns = [
        "q_seuil",
        "seuil_ravitaillement",
        "seuil_baisse_forte",
        "seuil_vitesse_arret_kmh",
        "seuil_distance_m",
        "seuil_temps_rapide_sec",
        "max_gap_refuel_sec",
    ]

    for column in threshold_columns:

        ok = compare_number(
            column,
            pandas_thresholds[
                column
            ],
            spark_thresholds[
                column
            ],
        )

        if not ok:
            problems.append(
                column
            )


    # ========================================================
    # 4. POPULATION DE REFERENCE
    # ========================================================

    print()
    print(
        "4. Population de référence"
    )

    reference_columns = [
        "nombre_variations_positives_reference",
        "nombre_variations_negatives_reference",
        "nombre_lignes_reference",
    ]

    for column in reference_columns:

        if (
            int(
                pandas_thresholds[
                    column
                ]
            )
            ==
            int(
                spark_thresholds[
                    column
                ]
            )
        ):

            print(
                f"[OK] {column} : "
                f"{pandas_thresholds[column]}"
            )

        else:

            print(
                f"[ERREUR] {column}"
            )

            print(
                "    Pandas :",
                pandas_thresholds[
                    column
                ],
            )

            print(
                "    Spark  :",
                spark_thresholds[
                    column
                ],
            )

            problems.append(
                column
            )


    pandas_excluded = sorted(
        str(value)
        for value in pandas_thresholds[
            "vehicles_excluded_from_thresholds"
        ]
    )

    spark_excluded = sorted(
        str(value)
        for value in spark_thresholds[
            "vehicles_excluded_from_thresholds"
        ]
    )

    if pandas_excluded == spark_excluded:

        print(
            "[OK] Véhicules exclus :",
            pandas_excluded,
        )

    else:

        print(
            "[ERREUR] Véhicules exclus"
        )

        print(
            "    Pandas :",
            pandas_excluded,
        )

        print(
            "    Spark  :",
            spark_excluded,
        )

        problems.append(
            "vehicles_excluded"
        )


    # ========================================================
    # 5. RESUME DES REGLES
    # ========================================================

    print()
    print(
        "5. Résumé des règles"
    )

    summary_columns = [
        "nombre_lignes_classifiees",
        "nombre_candidats_refuel",
        "nombre_episodes_refuel",
        "nombre_baisses_suspectes",
        "nombre_incoherences_transition",
    ]

    for column in summary_columns:

        pandas_value = int(
            pandas_summary[
                column
            ]
        )

        spark_value = int(
            spark_summary[
                column
            ]
        )

        if pandas_value == spark_value:

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
                column
            )


    # ========================================================
    # 6. EVENEMENTS PAR VEHICULE
    # ========================================================

    print()
    print(
        "6. Evénements par véhicule"
    )

    pandas_refuel_counts = (
        pandas_refuels
        .groupby(
            "deviceId"
        )
        .size()
        .to_dict()
    )

    spark_refuel_counts = (
        spark_refuels
        .groupby(
            "deviceId"
        )
        .size()
        .to_dict()
    )

    if pandas_refuel_counts == spark_refuel_counts:

        print(
            "[OK] Ravitaillements par véhicule :",
            pandas_refuel_counts,
        )

    else:

        print(
            "[ERREUR] Ravitaillements par véhicule"
        )

        print(
            "    Pandas :",
            pandas_refuel_counts,
        )

        print(
            "    Spark  :",
            spark_refuel_counts,
        )

        problems.append(
            "refuel_by_vehicle"
        )


    pandas_suspicious_counts = (
        pandas_suspicious
        .groupby(
            "deviceId"
        )
        .size()
        .to_dict()
    )

    spark_suspicious_counts = (
        spark_suspicious
        .groupby(
            "deviceId"
        )
        .size()
        .to_dict()
    )

    if (
        pandas_suspicious_counts
        ==
        spark_suspicious_counts
    ):

        print(
            "[OK] Baisses suspectes par véhicule :",
            pandas_suspicious_counts,
        )

    else:

        print(
            "[ERREUR] Baisses suspectes par véhicule"
        )

        print(
            "    Pandas :",
            pandas_suspicious_counts,
        )

        print(
            "    Spark  :",
            spark_suspicious_counts,
        )

        problems.append(
            "suspicious_by_vehicle"
        )


    # ========================================================
    # 7. AMPLITUDES DES BAISSES SUSPECTES
    # ========================================================

    print()
    print(
        "7. Amplitudes des baisses suspectes"
    )

    pandas_drops = sorted(
        np.round(
            pandas_suspicious[
                "drop_abs_pct"
            ]
            .astype(float)
            .to_numpy(),
            10,
        )
        .tolist()
    )

    spark_drops = sorted(
        np.round(
            spark_suspicious[
                "drop_abs_pct"
            ]
            .astype(float)
            .to_numpy(),
            10,
        )
        .tolist()
    )

    if pandas_drops == spark_drops:

        print(
            "[OK] Même ensemble de baisses suspectes"
        )

    else:

        print(
            "[ERREUR] Amplitudes différentes"
        )

        print(
            "    Pandas :",
            pandas_drops,
        )

        print(
            "    Spark  :",
            spark_drops,
        )

        problems.append(
            "suspicious_drop_values"
        )


    # ========================================================
    # 8. RESULTAT FINAL
    # ========================================================

    print()
    print(
        "=============================================="
    )

    if not problems:

        print(
            "TEST REGLES SPARK VS PANDAS : OK"
        )

    else:

        print(
            "TEST REGLES SPARK VS PANDAS : DIFFERENCES"
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