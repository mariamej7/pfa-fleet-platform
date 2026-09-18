from pathlib import Path
import sys

import pandas as pd


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
# IMPORTS DU PIPELINE
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
# DATASET
# ============================================================

SOURCE_DATASET = (
    PROJECT_ROOT
    / "data"
    / "uploads"
    / "199dea18e257444abc7f0e848806cc07.csv"
)

TEMP_DATASET = (
    PROJECT_ROOT
    / "data"
    / "uploads"
    / "test_zero_anomaly_input.csv"
)


# ============================================================
# VERIFICATION
# ============================================================

def check(
    name,
    actual,
    expected,
):

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

    print(
        "\n========================================"
    )

    print(
        "TEST PIPELINE SANS ANOMALIE CARBURANT"
    )

    print(
        "========================================\n"
    )

    if not SOURCE_DATASET.exists():

        raise FileNotFoundError(
            f"Dataset Oritech introuvable : {SOURCE_DATASET}"
        )

    try:

        # ----------------------------------------------------
        # 1. CREER UN DATASET DE TEST
        # ----------------------------------------------------

        print(
            "1. Creation du dataset de test"
        )

        raw = pd.read_csv(
            SOURCE_DATASET
        )

        # On garde toutes les vraies donnees :
        # dates, GPS, vitesse, odometre, ignition...
        #
        # On rend seulement le carburant constant.
        # Ainsi :
        # - aucun ravitaillement ;
        # - aucune baisse suspecte ;
        # - aucune baisse pour Isolation Forest.

        raw[
            "fuelLevel"
        ] = 50.0

        raw.to_csv(
            TEMP_DATASET,
            index=False,
        )

        print(
            "Lignes du dataset :",
            len(raw),
        )

        # ----------------------------------------------------
        # 2. PREPARATION
        # ----------------------------------------------------

        print(
            "\n2. Preparation"
        )

        df_prepared, preparation_report = (
            prepare_fleet_data(
                TEMP_DATASET
            )
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
            0,
        )

        # ----------------------------------------------------
        # 3. REGLES METIER
        # ----------------------------------------------------

        print(
            "\n3. Regles metier"
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
        )

        refueling_episodes = (
            rule_results[
                "refueling_episodes"
            ]
        )

        suspicious_events = (
            rule_results[
                "suspicious_events"
            ]
        )

        check(
            "Ravitaillements potentiels",
            len(
                refueling_episodes
            ),
            0,
        )

        check(
            "Baisses suspectes",
            len(
                suspicious_events
            ),
            0,
        )

        # ----------------------------------------------------
        # 4. ANALYSE CONTEXTUELLE
        # ----------------------------------------------------

        print(
            "\n4. Analyse contextuelle"
        )

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
            "Evenements contextuels",
            len(
                suspicious_events_analyzed
            ),
            0,
        )

        # ----------------------------------------------------
        # 5. ISOLATION FOREST
        # ----------------------------------------------------

        print(
            "\n5. Isolation Forest"
        )

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

        check(
            "Baisses analysees par IA",
            ai_results[
                "summary"
            ][
                "nombre_baisses_analysees"
            ],
            0,
        )

        check(
            "Candidats IA",
            ai_results[
                "summary"
            ][
                "nombre_candidats_ia"
            ],
            0,
        )

        check(
            "Modeles IA",
            ai_results[
                "summary"
            ][
                "nombre_modeles_entraines"
            ],
            0,
        )

        # ----------------------------------------------------
        # 6. KPI
        # ----------------------------------------------------

        print(
            "\n6. KPI"
        )

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
            "Vehicules KPI",
            len(
                kpi_vehicle
            ),
            3,
        )

        # ----------------------------------------------------
        # 7. TABLES PLATEFORME
        # ----------------------------------------------------

        print(
            "\n7. Tables plateforme"
        )

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
            "Ravitaillements finaux",
            len(
                platform_results[
                    "fact_refueling_events"
                ]
            ),
            0,
        )

        check(
            "Alertes finales",
            len(
                platform_results[
                    "fact_fuel_alerts"
                ]
            ),
            0,
        )

        check(
            "Evenements carburant",
            len(
                platform_results[
                    "fact_fuel_events"
                ]
            ),
            0,
        )

        check(
            "Problemes de cle",
            platform_results[
                "controls"
            ][
                "nombre_total_problemes"
            ],
            0,
        )

        # ----------------------------------------------------
        # RESULTAT
        # ----------------------------------------------------

        print(
            "\n========================================"
        )

        print(
            "TEST ZERO ANOMALIE COMPLET : OK"
        )

        print(
            "========================================"
        )

    finally:

        # Le fichier de test est temporaire.
        # On le supprime automatiquement.

        if TEMP_DATASET.exists():

            TEMP_DATASET.unlink()


if __name__ == "__main__":
    main()