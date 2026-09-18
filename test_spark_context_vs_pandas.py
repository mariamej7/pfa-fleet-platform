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
# IMPORTS
# ============================================================

from preprocessing.prepare_data import (
    prepare_fleet_data,
)

from anomaly_detection.rule_detection import (
    detect_rule_events,
)

from anomaly_detection.context_analysis import (
    analyze_suspicious_context,
)

from big_data.spark_processing import (
    create_spark_session,
    load_telemetry_spark,
    prepare_telemetry_spark,
)

from big_data.spark_rule_detection import (
    detect_rule_events_spark,
)

from big_data.spark_context_analysis import (
    analyze_suspicious_context_spark,
)


# ============================================================
# OUTIL COMPARAISON
# ============================================================

def normalize_counts(
    df,
    key_column,
    value_column="nombre_evenements",
):
    """
    Transforme un résumé en dictionnaire
    pour faciliter la comparaison.
    """

    if df is None or df.empty:
        return {}

    return {
        str(row[key_column]):
            int(row[value_column])

        for _, row in df.iterrows()
    }


# ============================================================
# DEBUT
# ============================================================

print()
print(
    "=============================================="
)
print(
    "TEST CONTEXTE SPARK VS PANDAS - ORITECH"
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

pandas_context = (
    analyze_suspicious_context(
        pandas_rules[
            "df_rules"
        ],
        pandas_rules[
            "suspicious_events"
        ],
    )
)

pandas_analyzed = (
    pandas_context[
        "suspicious_events_analyzed"
    ]
)

pandas_context_rows = (
    pandas_context[
        "suspicious_events_context_30min"
    ]
)

print(
    "[OK] Evénements analysés :",
    len(
        pandas_analyzed
    ),
)

print(
    "[OK] Lignes de contexte :",
    len(
        pandas_context_rows
    ),
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
            "PFA-Test-Context-Spark-vs-Pandas"
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

    spark_context = (
        analyze_suspicious_context_spark(
            spark_rules[
                "df_rules"
            ],
            spark_rules[
                "suspicious_events"
            ],
        )
    )

    spark_analyzed = (
        spark_context[
            "suspicious_events_analyzed"
        ]
    )

    spark_context_rows = (
        spark_context[
            "suspicious_events_context_30min"
        ]
    )

    print(
        "[OK] Evénements analysés :",
        len(
            spark_analyzed
        ),
    )

    print(
        "[OK] Lignes de contexte :",
        len(
            spark_context_rows
        ),
    )


    # ========================================================
    # 3. NOMBRES GENERAUX
    # ========================================================

    print()
    print(
        "3. Comparaison générale"
    )

    if (
        len(
            pandas_analyzed
        )
        ==
        len(
            spark_analyzed
        )
    ):

        print(
            "[OK] Même nombre d'événements analysés"
        )

    else:

        print(
            "[ERREUR] Nombre d'événements différent"
        )

        print(
            "    Pandas :",
            len(
                pandas_analyzed
            ),
        )

        print(
            "    Spark  :",
            len(
                spark_analyzed
            ),
        )

        problems.append(
            "nombre_evenements"
        )


    if (
        len(
            pandas_context_rows
        )
        ==
        len(
            spark_context_rows
        )
    ):

        print(
            "[OK] Même nombre de lignes de contexte"
        )

    else:

        print(
            "[ERREUR] Nombre de lignes de contexte différent"
        )

        print(
            "    Pandas :",
            len(
                pandas_context_rows
            ),
        )

        print(
            "    Spark  :",
            len(
                spark_context_rows
            ),
        )

        problems.append(
            "nombre_lignes_contexte"
        )


    # ========================================================
    # 4. IDS EVENEMENTS
    # ========================================================

    print()
    print(
        "4. Identifiants des événements"
    )

    pandas_ids = sorted(
        pandas_analyzed[
            "suspicious_event_id"
        ]
        .astype(str)
        .tolist()
    )

    spark_ids = sorted(
        spark_analyzed[
            "suspicious_event_id"
        ]
        .astype(str)
        .tolist()
    )

    if pandas_ids == spark_ids:

        print(
            "[OK] Même ensemble d'événements"
        )

    else:

        print(
            "[ERREUR] Identifiants différents"
        )

        print(
            "    Pandas :",
            pandas_ids,
        )

        print(
            "    Spark  :",
            spark_ids,
        )

        problems.append(
            "event_ids"
        )


    # ========================================================
    # 5. NIVEAUX DE CONFIANCE
    # ========================================================

    print()
    print(
        "5. Niveaux de confiance"
    )

    pandas_confidence = (
        normalize_counts(
            pandas_context[
                "confidence_summary"
            ],
            "confidence_level",
        )
    )

    spark_confidence = (
        normalize_counts(
            spark_context[
                "confidence_summary"
            ],
            "confidence_level",
        )
    )

    if (
        pandas_confidence
        ==
        spark_confidence
    ):

        print(
            "[OK] Même répartition :",
            pandas_confidence,
        )

    else:

        print(
            "[ERREUR] Répartition confiance différente"
        )

        print(
            "    Pandas :",
            pandas_confidence,
        )

        print(
            "    Spark  :",
            spark_confidence,
        )

        problems.append(
            "confidence_summary"
        )


    # ========================================================
    # 6. PERSISTANCE
    # ========================================================

    print()
    print(
        "6. Persistance"
    )

    pandas_persistence = (
        normalize_counts(
            pandas_context[
                "persistence_summary"
            ],
            "persistence",
        )
    )

    spark_persistence = (
        normalize_counts(
            spark_context[
                "persistence_summary"
            ],
            "persistence",
        )
    )

    if (
        pandas_persistence
        ==
        spark_persistence
    ):

        print(
            "[OK] Même répartition :",
            pandas_persistence,
        )

    else:

        print(
            "[ERREUR] Persistance différente"
        )

        print(
            "    Pandas :",
            pandas_persistence,
        )

        print(
            "    Spark  :",
            spark_persistence,
        )

        problems.append(
            "persistence_summary"
        )


    # ========================================================
    # 7. VALEURS PAR EVENEMENT
    # ========================================================

    print()
    print(
        "7. Comparaison événement par événement"
    )

    columns_to_compare = [
        "suspicious_event_id",
        "n_before_30min",
        "n_after_30min",
        "first_after_fuel_pct",
        "gap_to_first_after_sec",
        "median_after_30min_pct",
        "last_after_30min_pct",
        "recovery_ratio",
        "persistence",
        "context_support",
        "confidence_level",
    ]

    left = (
        pandas_analyzed[
            columns_to_compare
        ]
        .copy()
    )

    right = (
        spark_analyzed[
            columns_to_compare
        ]
        .copy()
    )

    comparison = left.merge(
        right,
        on="suspicious_event_id",
        how="outer",
        suffixes=(
            "_pandas",
            "_spark",
        ),
    )

    text_columns = [
        "persistence",
        "context_support",
        "confidence_level",
    ]

    numeric_columns = [
        "n_before_30min",
        "n_after_30min",
        "first_after_fuel_pct",
        "gap_to_first_after_sec",
        "median_after_30min_pct",
        "last_after_30min_pct",
        "recovery_ratio",
    ]

    for column in text_columns:

        a = (
            comparison[
                f"{column}_pandas"
            ]
            .fillna(
                "<NA>"
            )
            .astype(str)
        )

        b = (
            comparison[
                f"{column}_spark"
            ]
            .fillna(
                "<NA>"
            )
            .astype(str)
        )

        if (
            a == b
        ).all():

            print(
                f"[OK] {column}"
            )

        else:

            print(
                f"[ERREUR] {column}"
            )

            problems.append(
                column
            )


    for column in numeric_columns:

        a = pd.to_numeric(
            comparison[
                f"{column}_pandas"
            ],
            errors="coerce",
        )

        b = pd.to_numeric(
            comparison[
                f"{column}_spark"
            ],
            errors="coerce",
        )

        same_nan = (
            a.isna()
            &
            b.isna()
        )

        close_values = np.isclose(
            a.fillna(0),
            b.fillna(0),
            rtol=1e-8,
            atol=1e-8,
        )

        if (
            same_nan
            |
            close_values
        ).all():

            print(
                f"[OK] {column}"
            )

        else:

            print(
                f"[ERREUR] {column}"
            )

            problems.append(
                column
            )


    # ========================================================
    # 8. RESUME GLOBAL
    # ========================================================

    print()
    print(
        "8. Résumé global"
    )

    summary_columns = [
        "nombre_evenements_analyses",
        "nombre_lignes_contexte",
        "dates_invalides_dataset",
        "dates_invalides_evenements",
        "nombre_confiance_forte",
        "nombre_confiance_moyenne",
        "nombre_confiance_faible",
        "nombre_confiance_indeterminee",
    ]

    for column in summary_columns:

        pandas_value = (
            pandas_context[
                "summary"
            ][
                column
            ]
        )

        spark_value = (
            spark_context[
                "summary"
            ][
                column
            ]
        )

        if (
            pandas_value
            ==
            spark_value
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
                f"summary_{column}"
            )


    # ========================================================
    # 9. RESULTAT FINAL
    # ========================================================

    print()
    print(
        "=============================================="
    )

    if not problems:

        print(
            "TEST CONTEXTE SPARK VS PANDAS : OK"
        )

    else:

        print(
            "TEST CONTEXTE SPARK VS PANDAS : DIFFERENCES"
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