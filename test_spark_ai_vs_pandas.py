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
# IMPORTS PANDAS
# ============================================================

from preprocessing.prepare_data import (
    prepare_fleet_data,
)

from anomaly_detection.rule_detection import (
    detect_rule_events,
)

from anomaly_detection.isolation_forest import (
    detect_ai_anomalies,
)


# ============================================================
# IMPORTS SPARK
# ============================================================

from big_data.spark_processing import (
    create_spark_session,
    load_telemetry_spark,
    prepare_telemetry_spark,
)

from big_data.spark_rule_detection import (
    detect_rule_events_spark,
)

from big_data.spark_ai_detection import (
    detect_ai_anomalies_spark,
)


# ============================================================
# OUTILS
# ============================================================

def normalize_time_column(
    dataframe,
):
    """
    Normalise fixTime en UTC pour pouvoir
    comparer Pandas et Spark proprement.
    """

    result = dataframe.copy()

    if (
        "fixTime"
        in result.columns
    ):

        result[
            "fixTime"
        ] = pd.to_datetime(
            result[
                "fixTime"
            ],
            errors="coerce",
            utc=True,
        )

    return result


def build_keys(
    dataframe,
):
    """
    Construit des clés :
    deviceId + fixTime.
    """

    if (
        dataframe is None
        or dataframe.empty
    ):
        return []

    df = normalize_time_column(
        dataframe
    )

    return sorted(
        (
            str(row.deviceId),
            str(row.fixTime),
        )
        for row in (
            df[
                [
                    "deviceId",
                    "fixTime",
                ]
            ]
            .itertuples(
                index=False
            )
        )
    )


def compare_integer(
    label,
    pandas_value,
    spark_value,
    problems,
):
    pandas_value = int(
        pandas_value
    )

    spark_value = int(
        spark_value
    )

    if (
        pandas_value
        ==
        spark_value
    ):

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

        problems.append(
            label
        )


# ============================================================
# DEBUT
# ============================================================

print()
print(
    "=============================================="
)
print(
    "TEST IA SPARK VS PANDAS - ORITECH"
)
print(
    "=============================================="
)

problems = []


# ============================================================
# 1. PIPELINE PANDAS
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

pandas_ai = (
    detect_ai_anomalies(
        pandas_rules[
            "df_rules"
        ],
        pandas_rules[
            "suspicious_events"
        ],
    )
)

print(
    "[OK] Baisses candidates IA :",
    len(
        pandas_ai[
            "ai_candidates"
        ]
    ),
)

print(
    "[OK] Baisses analysées :",
    len(
        pandas_ai[
            "ai_scores"
        ]
    ),
)

print(
    "[OK] Candidats IA :",
    len(
        pandas_ai[
            "ai_top_candidates"
        ]
    ),
)


# ============================================================
# 2. PIPELINE SPARK
# ============================================================

print()
print(
    "2. Pipeline Spark"
)

spark = (
    create_spark_session(
        app_name=
            "PFA-Test-AI-Spark-vs-Pandas"
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

    spark_ai = (
        detect_ai_anomalies_spark(
            spark_rules[
                "df_rules"
            ],
            spark_rules[
                "suspicious_events"
            ],
        )
    )

    print(
        "[OK] Baisses candidates IA :",
        len(
            spark_ai[
                "ai_candidates"
            ]
        ),
    )

    print(
        "[OK] Baisses analysées :",
        len(
            spark_ai[
                "ai_scores"
            ]
        ),
    )

    print(
        "[OK] Candidats IA :",
        len(
            spark_ai[
                "ai_top_candidates"
            ]
        ),
    )


    # ========================================================
    # 3. NOMBRES GENERAUX
    # ========================================================

    print()
    print(
        "3. Comparaison générale"
    )

    compare_integer(
        "Nombre de candidats avant modèle",
        len(
            pandas_ai[
                "ai_candidates"
            ]
        ),
        len(
            spark_ai[
                "ai_candidates"
            ]
        ),
        problems,
    )

    compare_integer(
        "Nombre de baisses analysées",
        len(
            pandas_ai[
                "ai_scores"
            ]
        ),
        len(
            spark_ai[
                "ai_scores"
            ]
        ),
        problems,
    )

    compare_integer(
        "Nombre de candidats IA",
        len(
            pandas_ai[
                "ai_top_candidates"
            ]
        ),
        len(
            spark_ai[
                "ai_top_candidates"
            ]
        ),
        problems,
    )

    compare_integer(
        "Nombre de candidats IA uniquement",
        len(
            pandas_ai[
                "ai_only_candidates"
            ]
        ),
        len(
            spark_ai[
                "ai_only_candidates"
            ]
        ),
        problems,
    )


    # ========================================================
    # 4. RESUME GLOBAL
    # ========================================================

    print()
    print(
        "4. Résumé global"
    )

    integer_summary_columns = [
        "nombre_baisses_analysees",
        "nombre_candidats_ia",
        "nombre_alertes_regles",
        "nombre_overlap_regles_ia",
        "nombre_candidats_ia_uniquement",
        "nombre_modeles_entraines",
    ]

    for column in (
        integer_summary_columns
    ):

        compare_integer(
            column,
            pandas_ai[
                "summary"
            ][
                column
            ],
            spark_ai[
                "summary"
            ][
                column
            ],
            problems,
        )


    pandas_overlap_rate = float(
        pandas_ai[
            "summary"
        ][
            "taux_recouvrement_pct"
        ]
    )

    spark_overlap_rate = float(
        spark_ai[
            "summary"
        ][
            "taux_recouvrement_pct"
        ]
    )

    if np.isclose(
        pandas_overlap_rate,
        spark_overlap_rate,
        rtol=1e-10,
        atol=1e-10,
    ):

        print(
            "[OK] taux_recouvrement_pct :",
            pandas_overlap_rate,
        )

    else:

        print(
            "[ERREUR] taux_recouvrement_pct"
        )

        print(
            "    Pandas :",
            pandas_overlap_rate,
        )

        print(
            "    Spark  :",
            spark_overlap_rate,
        )

        problems.append(
            "taux_recouvrement_pct"
        )


    # ========================================================
    # 5. RESUME PAR VEHICULE
    # ========================================================

    print()
    print(
        "5. Résumé IA par véhicule"
    )

    pandas_vehicle = (
        pandas_ai[
            "ai_vehicle_summary"
        ]
        .sort_values(
            "deviceId"
        )
        .reset_index(
            drop=True
        )
    )

    spark_vehicle = (
        spark_ai[
            "ai_vehicle_summary"
        ]
        .sort_values(
            "deviceId"
        )
        .reset_index(
            drop=True
        )
    )

    vehicle_columns = [
        "nb_baisses_analysees",
        "nb_candidats_ia",
        "nb_alertes_regles",
        "nb_overlap_regles_ia",
    ]

    all_devices = sorted(
        set(
            pandas_vehicle[
                "deviceId"
            ]
            .astype(str)
        )
        |
        set(
            spark_vehicle[
                "deviceId"
            ]
            .astype(str)
        )
    )

    for device_id in all_devices:

        p = (
            pandas_vehicle[
                pandas_vehicle[
                    "deviceId"
                ].astype(str)
                ==
                device_id
            ]
        )

        s = (
            spark_vehicle[
                spark_vehicle[
                    "deviceId"
                ].astype(str)
                ==
                device_id
            ]
        )

        if (
            p.empty
            or s.empty
        ):

            print(
                f"[ERREUR] véhicule {device_id}"
            )

            problems.append(
                f"vehicle_{device_id}"
            )

            continue

        print(
            f"Véhicule {device_id}"
        )

        for column in vehicle_columns:

            pandas_value = int(
                p.iloc[0][
                    column
                ]
            )

            spark_value = int(
                s.iloc[0][
                    column
                ]
            )

            if (
                pandas_value
                ==
                spark_value
            ):

                print(
                    f"  [OK] {column} : "
                    f"{pandas_value}"
                )

            else:

                print(
                    f"  [ERREUR] {column}"
                )

                print(
                    "      Pandas :",
                    pandas_value,
                )

                print(
                    "      Spark  :",
                    spark_value,
                )

                problems.append(
                    f"{device_id}_{column}"
                )


    # ========================================================
    # 6. MEMES BAISSES TRANSMISES A L'IA
    # ========================================================

    print()
    print(
        "6. Baisses transmises à Isolation Forest"
    )

    pandas_candidate_keys = (
        build_keys(
            pandas_ai[
                "ai_candidates"
            ]
        )
    )

    spark_candidate_keys = (
        build_keys(
            spark_ai[
                "ai_candidates"
            ]
        )
    )

    if (
        pandas_candidate_keys
        ==
        spark_candidate_keys
    ):

        print(
            "[OK] Même ensemble de baisses"
        )

    else:

        print(
            "[ERREUR] Les baisses transmises à l'IA diffèrent"
        )

        print(
            "    Pandas :",
            len(
                pandas_candidate_keys
            ),
        )

        print(
            "    Spark  :",
            len(
                spark_candidate_keys
            ),
        )

        problems.append(
            "ai_candidate_keys"
        )


    # ========================================================
    # 7. MEMES CANDIDATS IA
    # ========================================================

    print()
    print(
        "7. Top 1 % Isolation Forest"
    )

    pandas_top_keys = (
        build_keys(
            pandas_ai[
                "ai_top_candidates"
            ]
        )
    )

    spark_top_keys = (
        build_keys(
            spark_ai[
                "ai_top_candidates"
            ]
        )
    )

    if (
        pandas_top_keys
        ==
        spark_top_keys
    ):

        print(
            "[OK] Même ensemble de candidats IA"
        )

    else:

        print(
            "[ERREUR] Les candidats IA diffèrent"
        )

        print(
            "    Pandas :",
            len(
                pandas_top_keys
            ),
        )

        print(
            "    Spark  :",
            len(
                spark_top_keys
            ),
        )

        problems.append(
            "ai_top_keys"
        )


    # ========================================================
    # 8. IA UNIQUEMENT
    # ========================================================

    print()
    print(
        "8. Candidats IA uniquement"
    )

    pandas_only_keys = (
        build_keys(
            pandas_ai[
                "ai_only_candidates"
            ]
        )
    )

    spark_only_keys = (
        build_keys(
            spark_ai[
                "ai_only_candidates"
            ]
        )
    )

    if (
        pandas_only_keys
        ==
        spark_only_keys
    ):

        print(
            "[OK] Même ensemble IA uniquement"
        )

    else:

        print(
            "[ERREUR] Les candidats IA uniquement diffèrent"
        )

        problems.append(
            "ai_only_keys"
        )


    # ========================================================
    # 9. COMPARAISON REGLES / IA
    # ========================================================

    print()
    print(
        "9. Recouvrement règles / IA"
    )

    pandas_comparison = (
        pandas_ai[
            "rules_vs_ai_comparison"
        ]
        .copy()
    )

    spark_comparison = (
        spark_ai[
            "rules_vs_ai_comparison"
        ]
        .copy()
    )

    pandas_rule_ids = sorted(
        pandas_comparison[
            "suspicious_event_id"
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

    spark_rule_ids = sorted(
        spark_comparison[
            "suspicious_event_id"
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

    if (
        pandas_rule_ids
        ==
        spark_rule_ids
    ):

        print(
            "[OK] Même ensemble d'alertes règles"
        )

    else:

        print(
            "[ERREUR] Alertes règles différentes"
        )

        problems.append(
            "rule_ids"
        )


    pandas_overlap_ids = sorted(
        pandas_comparison.loc[
            pandas_comparison[
                "ai_anomaly_flag"
            ]
            .fillna(
                False
            )
            .astype(
                bool
            ),
            "suspicious_event_id",
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

    spark_overlap_ids = sorted(
        spark_comparison.loc[
            spark_comparison[
                "ai_anomaly_flag"
            ]
            .fillna(
                False
            )
            .astype(
                bool
            ),
            "suspicious_event_id",
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

    if (
        pandas_overlap_ids
        ==
        spark_overlap_ids
    ):

        print(
            "[OK] Même ensemble Règle + IA"
        )

    else:

        print(
            "[ERREUR] Recouvrements différents"
        )

        print(
            "    Pandas :",
            pandas_overlap_ids,
        )

        print(
            "    Spark  :",
            spark_overlap_ids,
        )

        problems.append(
            "overlap_ids"
        )


    # ========================================================
    # 10. RESULTAT FINAL
    # ========================================================

    print()
    print(
        "=============================================="
    )

    if not problems:

        print(
            "TEST IA SPARK VS PANDAS : OK"
        )

    else:

        print(
            "TEST IA SPARK VS PANDAS : DIFFERENCES"
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