from pathlib import Path
import sys


# ============================================================
# CHEMINS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
PIPELINE_DIR = PROJECT_ROOT / "pipeline"

if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(PIPELINE_DIR),
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

from anomaly_detection.isolation_forest import (
    detect_ai_anomalies,
)


# ============================================================
# DATASET ORITECH
# ============================================================

DATASET = (
    PROJECT_ROOT
    / "data"
    / "uploads"
    / "199dea18e257444abc7f0e848806cc07.csv"
)


# ============================================================
# TEST
# ============================================================

def main():

    print(
        "\n===== TEST ZERO BAISSE IA ====="
    )

    # --------------------------------------------------------
    # Preparation normale
    # --------------------------------------------------------

    df_prepared, _ = (
        prepare_fleet_data(
            DATASET
        )
    )

    rule_results = (
        detect_rule_events(
            df_prepared
        )
    )

    df_rules = (
        rule_results[
            "df_rules"
        ]
        .copy()
    )

    # --------------------------------------------------------
    # Simulation :
    # aucune diminution exploitable
    # --------------------------------------------------------

    df_rules[
        "delta_fuel"
    ] = 0.0

    # Pas d'alertes regles pour ce test.
    suspicious_events = (
        rule_results[
            "suspicious_events"
        ]
        .iloc[0:0]
        .copy()
    )

    print(
        "Baisses negatives simulees :",
        int(
            (
                df_rules[
                    "delta_fuel"
                ] < 0
            ).sum()
        ),
    )

    # --------------------------------------------------------
    # Isolation Forest
    # --------------------------------------------------------

    result = (
        detect_ai_anomalies(
            df_rules,
            suspicious_events,
        )
    )

    print(
        "Baisses analysees par IA :",
        result[
            "summary"
        ][
            "nombre_baisses_analysees"
        ],
    )

    print(
        "Candidats IA :",
        result[
            "summary"
        ][
            "nombre_candidats_ia"
        ],
    )

    print(
        "Modeles entraines :",
        result[
            "summary"
        ][
            "nombre_modeles_entraines"
        ],
    )

    print(
        "\nTEST TERMINE"
    )


if __name__ == "__main__":
    main()