from pathlib import Path
import sys


# ============================================================
# CHEMINS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
PIPELINE_DIR = PROJECT_ROOT / "pipeline"

if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))


# ============================================================
# IMPORTS DU PIPELINE
# ============================================================

from preprocessing.prepare_data import prepare_fleet_data

from anomaly_detection.rule_detection import (
    detect_rule_events,
)

from anomaly_detection.context_analysis import (
    analyze_suspicious_context,
)

from anomaly_detection.isolation_forest import (
    detect_ai_anomalies,
)

from analytics.compute_kpis import (
    compute_fleet_kpis,
)

from platform_tables.prepare_platform_tables import (
    prepare_platform_tables,
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
# FONCTION DE VERIFICATION
# ============================================================

def check(name, actual, expected):

    if actual != expected:

        raise AssertionError(
            f"{name} : attendu={expected}, obtenu={actual}"
        )

    print(
        f"[OK] {name} : {actual}"
    )


# ============================================================
# TEST COMPLET
# ============================================================

def main():

    print("\n===== TEST PIPELINE ORITECH =====\n")

    if not DATASET.exists():

        raise FileNotFoundError(
            f"Dataset introuvable : {DATASET}"
        )

    # --------------------------------------------------------
    # 1. PREPARATION
    # --------------------------------------------------------

    print("1. Preparation")

    df_prepared, preparation_report = (
        prepare_fleet_data(
            DATASET
        )
    )

    check(
        "Lignes preparees",
        len(df_prepared),
        318494,
    )

    check(
        "Vehicules",
        preparation_report[
            "nombre_vehicules"
        ],
        3,
    )

    check(
        "Fuel hors plage",
        preparation_report[
            "nombre_fuel_hors_plage"
        ],
        2084,
    )

    # --------------------------------------------------------
    # 2. REGLES
    # --------------------------------------------------------

    print("\n2. Regles metier")

    rule_results = detect_rule_events(
        df_prepared
    )

    df_rules = rule_results[
        "df_rules"
    ]

    refueling_episodes = rule_results[
        "refueling_episodes"
    ]

    suspicious_events = rule_results[
        "suspicious_events"
    ]

    check(
        "Ravitaillements potentiels",
        len(refueling_episodes),
        28,
    )

    check(
        "Baisses suspectes",
        len(suspicious_events),
        15,
    )

    # --------------------------------------------------------
    # 3. CONTEXTE
    # --------------------------------------------------------

    print("\n3. Analyse contextuelle")

    context_results = (
        analyze_suspicious_context(
            df_rules,
            suspicious_events,
        )
    )

    suspicious_events_analyzed = (
        context_results[
            "suspicious_events_analyzed"
        ]
    )

    check(
        "Evenements analyses",
        len(
            suspicious_events_analyzed
        ),
        15,
    )

    # --------------------------------------------------------
    # 4. IA
    # --------------------------------------------------------

    print("\n4. Isolation Forest")

    ai_results = (
        detect_ai_anomalies(
            df_rules,
            suspicious_events,
        )
    )

    ai_top_candidates = (
        ai_results[
            "ai_top_candidates"
        ]
    )

    rules_vs_ai_comparison = (
        ai_results[
            "rules_vs_ai_comparison"
        ]
    )

    ai_vehicle_summary = (
        ai_results[
            "ai_vehicle_summary"
        ]
    )

    ai_summary = ai_results[
        "summary"
    ]

    check(
        "Baisses analysees par IA",
        int(
            ai_summary[
                "nombre_baisses_analysees"
            ]
        ),
        6247,
    )

    check(
        "Candidats IA",
        int(
            ai_summary[
                "nombre_candidats_ia"
            ]
        ),
        64,
    )

    check(
        "Regle + IA",
        int(
            ai_summary[
                "nombre_overlap_regles_ia"
            ]
        ),
        14,
    )

    # --------------------------------------------------------
    # 5. KPI
    # --------------------------------------------------------

    print("\n5. KPI")

    kpi_results = (
        compute_fleet_kpis(
            df_rules,
            refueling_episodes=
                refueling_episodes,
            suspicious_events=
                suspicious_events,
        )
    )

    kpi_vehicle = (
        kpi_results[
            "kpi_vehicle"
        ]
    )

    kpi_daily = (
        kpi_results[
            "kpi_daily"
        ]
    )

    kpi_global = (
        kpi_results[
            "kpi_global"
        ]
    )

    check(
        "KPI journaliers",
        len(kpi_daily),
        99,
    )

    # --------------------------------------------------------
    # 6. TABLES PLATEFORME
    # --------------------------------------------------------

    print("\n6. Tables plateforme")

    platform_results = (
        prepare_platform_tables(
            kpi_vehicle=
                kpi_vehicle,

            kpi_daily=
                kpi_daily,

            kpi_global=
                kpi_global,

            refueling_episodes=
                refueling_episodes,

            suspicious_events_analyzed=
                suspicious_events_analyzed,

            ai_top_candidates=
                ai_top_candidates,

            rules_vs_ai_comparison=
                rules_vs_ai_comparison,

            ai_vehicle_summary=
                ai_vehicle_summary,
        )
    )

    check(
        "Alertes finales",
        len(
            platform_results[
                "fact_fuel_alerts"
            ]
        ),
        65,
    )

    check(
        "Evenements carburant",
        len(
            platform_results[
                "fact_fuel_events"
            ]
        ),
        93,
    )

    check(
        "Alertes P1",
        int(
            platform_results[
                "summary"
            ][
                "nombre_alertes_p1"
            ]
        ),
        8,
    )

    check(
        "Problemes de cle",
        int(
            platform_results[
                "controls"
            ][
                "nombre_total_problemes"
            ]
        ),
        0,
    )

    print(
        "\n============================="
    )

    print(
        "TEST ORITECH COMPLET : OK"
    )

    print(
        "============================="
    )


if __name__ == "__main__":
    main()