import argparse
from pprint import pprint

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

def main():

    parser = argparse.ArgumentParser(
        description="Pipeline Data - Analyse de flotte Oritech"
    )

    parser.add_argument(
        "file_path",
        help="Chemin du fichier CSV ou Parquet.",
    )

    args = parser.parse_args()

    print()
    print("=" * 75)
    print("PFA ORITECH - PIPELINE DATA")
    print("=" * 75)

    # ========================================================
    # ETAPE 1 - PREPARATION DES DONNEES
    # ========================================================

    print()
    print("ETAPE 1 - PREPARATION DES DONNEES")
    print("-" * 75)

    df_prepared, rapport = prepare_fleet_data(
        args.file_path
    )

    print(
        f"Lignes brutes              : "
        f"{rapport['nombre_lignes_brutes']:,}"
    )

    print(
        f"Doublons supprimés         : "
        f"{rapport['nombre_doublons_supprimes']:,}"
    )

    print(
        f"Lignes préparées           : "
        f"{rapport['nombre_lignes_preparees']:,}"
    )

    print(
        f"Nombre de véhicules        : "
        f"{rapport['nombre_vehicules']}"
    )

    print(
        f"Dates invalides            : "
        f"{rapport['nombre_dates_invalides']:,}"
    )

    print(
        f"Fuel hors plage 0-100 %    : "
        f"{rapport['nombre_fuel_hors_plage']:,}"
    )

    print()
    print("Valeurs manquantes :")

    pprint(
        rapport["valeurs_manquantes"],
        sort_dicts=False,
    )

    # ========================================================
    # ETAPE 2 - DETECTION PAR REGLES
    # ========================================================

    print()
    print("=" * 75)
    print("ETAPE 2 - DETECTION PAR REGLES")
    print("-" * 75)

    rule_results = detect_rule_events(
        df_prepared
    )

    df_rules = rule_results[
        "df_rules"
    ]

    thresholds = rule_results[
        "thresholds"
    ]

    refueling_episodes = rule_results[
        "refueling_episodes"
    ]

    suspicious_events = rule_results[
        "suspicious_events"
    ]

    rule_summary = rule_results[
        "summary"
    ]

    print()
    print("SEUILS CALCULES")
    print("-" * 75)

    print(
        f"Seuil hausse extrême             : "
        f"{thresholds['seuil_ravitaillement']:.3f} points %"
    )

    print(
        f"Seuil baisse extrême             : "
        f"{thresholds['seuil_baisse_forte']:.3f} points %"
    )

    print(
        f"Seuil vitesse proche arrêt       : "
        f"{thresholds['seuil_vitesse_arret_kmh']:.3f} km/h"
    )

    print(
        "Véhicules exclus du calcul "
        "des seuils                  :",
        thresholds[
            "vehicles_excluded_from_thresholds"
        ],
    )

    print()
    print("RESULTATS DES REGLES")
    print("-" * 75)

    print(
        f"Candidats ravitaillement         : "
        f"{rule_summary['nombre_candidats_refuel']}"
    )

    print(
        f"Ravitaillements potentiels       : "
        f"{rule_summary['nombre_episodes_refuel']}"
    )

    print(
        f"Baisses suspectes                : "
        f"{rule_summary['nombre_baisses_suspectes']}"
    )

    # ========================================================
    # ETAPE 3 - ANALYSE CONTEXTUELLE
    # ========================================================

    print()
    print("=" * 75)
    print("ETAPE 3 - ANALYSE CONTEXTUELLE")
    print("-" * 75)

    context_results = analyze_suspicious_context(
        df_rules,
        suspicious_events,
    )

    suspicious_events_analyzed = (
        context_results[
            "suspicious_events_analyzed"
        ]
    )

    context_summary = context_results[
        "summary"
    ]

    print(
        f"Événements analysés        : "
        f"{context_summary['nombre_evenements_analyses']}"
    )

    print(
        f"Confiance Forte            : "
        f"{context_summary['nombre_confiance_forte']}"
    )

    print(
        f"Confiance Moyenne          : "
        f"{context_summary['nombre_confiance_moyenne']}"
    )

    print(
        f"Confiance Faible           : "
        f"{context_summary['nombre_confiance_faible']}"
    )

    print(
        f"Confiance Indéterminée     : "
        f"{context_summary['nombre_confiance_indeterminee']}"
    )

    # ========================================================
    # ETAPE 4 - ISOLATION FOREST
    # ========================================================

    print()
    print("=" * 75)
    print("ETAPE 4 - DETECTION IA : ISOLATION FOREST")
    print("-" * 75)

    ai_results = detect_ai_anomalies(
        df_rules,
        suspicious_events,
    )

    ai_summary = ai_results[
        "summary"
    ]

    ai_vehicle_summary = ai_results[
        "ai_vehicle_summary"
    ]

    ai_top_candidates = ai_results[
        "ai_top_candidates"
    ]

    rules_vs_ai_comparison = ai_results[
        "rules_vs_ai_comparison"
    ]

    print(
        f"Baisses analysées          : "
        f"{ai_summary['nombre_baisses_analysees']:,}"
    )

    print(
        f"Candidats IA               : "
        f"{ai_summary['nombre_candidats_ia']}"
    )

    print(
        f"Alertes règles             : "
        f"{ai_summary['nombre_alertes_regles']}"
    )

    print(
        f"Règle + IA                 : "
        f"{ai_summary['nombre_overlap_regles_ia']}"
    )

    print(
        f"Taux de recouvrement       : "
        f"{ai_summary['taux_recouvrement_pct']:.2f} %"
    )

    print()
    print(
        "Ce taux est un taux de recouvrement, "
        "pas une accuracy."
    )

    # ========================================================
    # ETAPE 5 - KPI
    # ========================================================

    print()
    print("=" * 75)
    print("ETAPE 5 - CALCUL DES KPI")
    print("-" * 75)

    kpi_results = compute_fleet_kpis(
        df_rules,
        refueling_episodes=
            refueling_episodes,
        suspicious_events=
            suspicious_events,
    )

    kpi_vehicle = kpi_results[
        "kpi_vehicle"
    ]

    kpi_daily = kpi_results[
        "kpi_daily"
    ]

    kpi_global = kpi_results[
        "kpi_global"
    ]

    print(
        f"Véhicules                  : "
        f"{kpi_global['nombre_vehicules']}"
    )

    print(
        f"Mesures                    : "
        f"{kpi_global['nombre_total_mesures']:,}"
    )

    print(
        f"Distance totale            : "
        f"{kpi_global['distance_totale_km']:,.3f} km"
    )

    print(
        f"Ravitaillements potentiels : "
        f"{kpi_global['nb_ravitaillements_potentiels']}"
    )

    print(
        f"Baisses suspectes          : "
        f"{kpi_global['nb_baisses_suspectes']}"
    )

    print(
        f"Incohérences fuelLevel     : "
        f"{kpi_global['nb_incoherences_fuel']:,}"
    )

    # ========================================================
    # ETAPE 6 - PREPARATION DES TABLES PLATEFORME
    # ========================================================

    print()
    print("=" * 75)
    print("ETAPE 6 - PREPARATION DES TABLES PLATEFORME")
    print("-" * 75)

    platform_results = prepare_platform_tables(
        kpi_vehicle=kpi_vehicle,
        kpi_daily=kpi_daily,
        kpi_global=kpi_global,
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

    dim_vehicles = platform_results[
        "dim_vehicles"
    ]

    fact_fleet_daily = platform_results[
        "fact_fleet_daily"
    ]

    fact_refueling_events = platform_results[
        "fact_refueling_events"
    ]

    fact_fuel_alerts = platform_results[
        "fact_fuel_alerts"
    ]

    fact_fuel_events = platform_results[
        "fact_fuel_events"
    ]

    fleet_summary = platform_results[
        "fleet_summary"
    ]

    controls = platform_results[
        "controls"
    ]

    platform_summary = platform_results[
        "summary"
    ]

    # ========================================================
    # RESULTATS DES TABLES
    # ========================================================

    print()
    print("TABLES GENEREES")
    print("-" * 75)

    print(
        f"dim_vehicles              : "
        f"{len(dim_vehicles)} lignes"
    )

    print(
        f"fact_fleet_daily          : "
        f"{len(fact_fleet_daily)} lignes"
    )

    print(
        f"fact_refueling_events     : "
        f"{len(fact_refueling_events)} lignes"
    )

    print(
        f"fact_fuel_alerts          : "
        f"{len(fact_fuel_alerts)} lignes"
    )

    print(
        f"fact_fuel_events          : "
        f"{len(fact_fuel_events)} lignes"
    )

    print(
        f"fleet_summary             : "
        f"{len(fleet_summary)} ligne"
    )

    # ========================================================
    # PRIORITES
    # ========================================================

    print()
    print("PRIORITES DES ALERTES")
    print("-" * 75)

    priority_counts = (
        fact_fuel_alerts[
            "priorite_alerte"
        ]
        .value_counts()
    )

    print(
        priority_counts.to_string()
    )

    print()
    print(
        f"P1 Critiques              : "
        f"{platform_summary['nombre_alertes_p1']}"
    )

    print(
        f"P2 Élevées                : "
        f"{platform_summary['nombre_alertes_p2']}"
    )

    print(
        f"P3 À investiguer          : "
        f"{platform_summary['nombre_alertes_p3']}"
    )

    print(
        f"P4 Faibles                : "
        f"{platform_summary['nombre_alertes_p4']}"
    )

    print(
        f"P5 Prudence               : "
        f"{platform_summary['nombre_alertes_p5']}"
    )

    # ========================================================
    # CONTROLES D'UNICITE
    # ========================================================

    print()
    print("CONTROLES DE QUALITE")
    print("-" * 75)

    pprint(
        controls,
        sort_dicts=False,
    )

    # ========================================================
    # VERIFICATION AUTOMATIQUE DU DATASET DE VALIDATION
    # ========================================================

    print()
    print("=" * 75)
    print("VERIFICATION DU DATASET DE VALIDATION")
    print("-" * 75)

    expected = {
        "dim_vehicles": 3,
        "fact_fleet_daily": 99,
        "fact_refueling_events": 28,
        "fact_fuel_alerts": 65,
        "fact_fuel_events": 93,
        "fleet_summary": 1,
    }

    actual = {
        "dim_vehicles":
            len(dim_vehicles),

        "fact_fleet_daily":
            len(fact_fleet_daily),

        "fact_refueling_events":
            len(fact_refueling_events),

        "fact_fuel_alerts":
            len(fact_fuel_alerts),

        "fact_fuel_events":
            len(fact_fuel_events),

        "fleet_summary":
            len(fleet_summary),
    }

    all_ok = True

    for table_name, expected_count in (
        expected.items()
    ):

        actual_count = actual[
            table_name
        ]

        status = (
            "OK"
            if actual_count
            == expected_count
            else "ECART"
        )

        if (
            actual_count
            != expected_count
        ):
            all_ok = False

        print(
            f"{table_name:<25} "
            f"{actual_count:>4} "
            f"/ attendu {expected_count:<4} "
            f"→ {status}"
        )

    # ========================================================
    # VERIFICATION DOUBLONS
    # ========================================================

    if (
        controls[
            "nombre_total_problemes"
        ] == 0
    ):

        print()
        print(
            "Aucun doublon détecté "
            "sur les clés principales."
        )

    else:

        all_ok = False

        print()
        print(
            "ATTENTION : un problème "
            "d'unicité a été détecté."
        )

    # ========================================================
    # RESULTAT FINAL
    # ========================================================

    print()
    print("=" * 75)

    if all_ok:

        print(
            "PIPELINE COMPLET VALIDE AVEC SUCCES"
        )

        print()
        print(
            "Résultats attendus : "
            "3 / 99 / 28 / 65 / 93 / 1"
        )

    else:

        print(
            "PIPELINE EXECUTE, MAIS "
            "DES ECARTS SONT A VERIFIER"
        )

    print("=" * 75)


if __name__ == "__main__":
    main()