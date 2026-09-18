from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
PIPELINE_DIR = PROJECT_ROOT / "pipeline"

if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(PIPELINE_DIR),
    )


from preprocessing.prepare_data import prepare_fleet_data

from anomaly_detection.rule_detection import (
    detect_rule_events,
)

from anomaly_detection.context_analysis import (
    analyze_suspicious_context,
)


DATASET = (
    PROJECT_ROOT
    / "data"
    / "uploads"
    / "199dea18e257444abc7f0e848806cc07.csv"
)


def main():

    print(
        "\n===== TEST ZERO EVENEMENT CONTEXTUEL ====="
    )

    df_prepared, _ = prepare_fleet_data(
        DATASET
    )

    rule_results = detect_rule_events(
        df_prepared
    )

    df_rules = rule_results[
        "df_rules"
    ]

    suspicious_events = rule_results[
        "suspicious_events"
    ]

    # On garde exactement la structure réelle,
    # mais on retire toutes les lignes.
    zero_events = (
        suspicious_events
        .iloc[0:0]
        .copy()
    )

    print(
        "Evenements envoyes :",
        len(zero_events),
    )

    result = analyze_suspicious_context(
        df_rules,
        zero_events,
    )

    analyzed = result[
        "suspicious_events_analyzed"
    ]

    print(
        "Evenements analyses :",
        len(analyzed),
    )

    print(
        "Colonnes retournees :",
        analyzed.columns.tolist(),
    )

    print(
        "Colonne confidence_level presente :",
        "confidence_level"
        in analyzed.columns,
    )

    print(
        "\nTEST TERMINE"
    )


if __name__ == "__main__":
    main()