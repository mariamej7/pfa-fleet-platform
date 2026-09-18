from typing import Dict

import numpy as np
import pandas as pd


# ============================================================
# COLONNES FINALES DES ALERTES
# ============================================================

ALERT_COLUMNS = [
    "deviceId",
    "fixTime",
    "alert_type",
    "source_detection",
    "suspicious_event_id",
    "fuelLevel",
    "drop_abs_pct",
    "delta_time_sec",
    "speed_kmh",
    "distance_abs_m",
    "ignition",
    "ai_anomaly_score",
    "ai_score_percentile",
    "contexte_temporel",
    "latitude",
    "longitude",
    "detection_combinee",
    "ai_anomaly_flag",
    "persistence",
    "context_support",
    "confidence_level",
    "analysis_reason",
    "fuel_before_pct",
    "fuel_event_pct",
    "recovery_ratio",
    "lien_carte",
    "alert_id",
    "rang_priorite",
    "priorite_alerte",
    "raison_priorite",
    "statut_validation",
]


# ============================================================
# COLONNES FINALES DES RAVITAILLEMENTS
# ============================================================

REFUEL_COLUMNS = [
    "refuel_episode_id",
    "deviceId",
    "start_time",
    "end_time",
    "duration_sec",
    "n_steps",
    "start_fuel_pct",
    "end_fuel_pct",
    "total_delta_fuel_pct",
    "max_speed_kmh",
    "mean_speed_kmh",
    "event_id",
    "event_time",
    "event_category",
    "source_detection",
    "variation_fuel_pct",
    "fuel_level_pct",
]


# ============================================================
# COLONNES TABLE UNIQUE DES EVENEMENTS CARBURANT
# ============================================================

FUEL_EVENT_COLUMNS = [
    "event_id",
    "deviceId",
    "event_time",
    "event_category",
    "source_detection",
    "priorite_alerte",
    "variation_fuel_pct",
    "fuel_level_pct",
    "confidence_level",
    "ai_score_percentile",
    "latitude",
    "longitude",
    "lien_carte",
]


# ============================================================
# OUTILS
# ============================================================

def ensure_columns(
    dataframe: pd.DataFrame,
    columns,
) -> pd.DataFrame:
    """
    Ajoute les colonnes manquantes avec NaN.

    Cette fonction permet aux autres étapes
    de fonctionner même lorsqu'un DataFrame
    est vide ou ne contient pas toutes
    les colonnes attendues.
    """

    result = dataframe.copy()

    for column in columns:

        if column not in result.columns:

            result[
                column
            ] = np.nan

    return result


def convert_boolean_series(
    values: pd.Series,
) -> pd.Series:
    """
    Convertit proprement une série
    en valeurs booléennes.
    """

    if pd.api.types.is_bool_dtype(
        values
    ):

        return (
            values
            .fillna(False)
            .astype(bool)
        )

    return (
        values
        .astype(str)
        .str.strip()
        .str.lower()
        .map(
            {
                "true": True,
                "false": False,
                "1": True,
                "0": False,
            }
        )
        .fillna(False)
        .astype(bool)
    )


# ============================================================
# DIMENSION VEHICULES
# ============================================================

def build_dim_vehicles(
    kpi_vehicle: pd.DataFrame,
    ai_vehicle_summary: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construit une ligne de synthèse
    par véhicule.
    """

    vehicles = (
        kpi_vehicle.copy()
    )

    ai_summary = (
        ai_vehicle_summary.copy()
    )

    # --------------------------------------------------------
    # CAS : AUCUN RESULTAT IA
    # --------------------------------------------------------

    if ai_summary.empty:

        vehicles[
            "nb_baisses_analysees"
        ] = 0

        vehicles[
            "nb_candidats_ia"
        ] = 0

        vehicles[
            "nb_alertes_regles"
        ] = 0

        vehicles[
            "nb_overlap_regles_ia"
        ] = 0

    else:

        vehicles = (
            vehicles.merge(
                ai_summary,
                on="deviceId",
                how="left",
                validate="one_to_one",
            )
        )

    # --------------------------------------------------------
    # COLONNES IA
    # --------------------------------------------------------

    ai_count_columns = [
        "nb_baisses_analysees",
        "nb_candidats_ia",
        "nb_alertes_regles",
        "nb_overlap_regles_ia",
    ]

    for column in ai_count_columns:

        if (
            column
            not in vehicles.columns
        ):

            vehicles[
                column
            ] = 0

        vehicles[
            column
        ] = (
            vehicles[
                column
            ]
            .fillna(0)
            .astype(int)
        )

    # --------------------------------------------------------
    # ALERTES IA UNIQUEMENT
    # --------------------------------------------------------

    vehicles[
        "nb_alertes_ia_uniquement"
    ] = (
        vehicles[
            "nb_candidats_ia"
        ]
        -
        vehicles[
            "nb_overlap_regles_ia"
        ]
    )

    # --------------------------------------------------------
    # ALERTES REGLES UNIQUEMENT
    # --------------------------------------------------------

    vehicles[
        "nb_alertes_regle_uniquement"
    ] = (
        vehicles[
            "nb_alertes_regles"
        ]
        -
        vehicles[
            "nb_overlap_regles_ia"
        ]
    )

    # --------------------------------------------------------
    # TRI
    # --------------------------------------------------------

    if (
        "deviceId"
        in vehicles.columns
    ):

        vehicles = (
            vehicles
            .sort_values(
                "deviceId"
            )
            .reset_index(
                drop=True
            )
        )

    return vehicles


# ============================================================
# KPI JOURNALIERS
# ============================================================

def build_fact_fleet_daily(
    kpi_daily: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prépare les KPI journaliers
    et ajoute les variables calendrier.
    """

    daily = (
        kpi_daily.copy()
    )

    # --------------------------------------------------------
    # CAS VIDE
    # --------------------------------------------------------

    if daily.empty:

        return daily

    # --------------------------------------------------------
    # GARANTIR LES COLONNES IMPORTANTES
    # --------------------------------------------------------

    daily = ensure_columns(
        daily,
        [
            "deviceId",
            "date",
        ],
    )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    daily[
        "date"
    ] = pd.to_datetime(
        daily[
            "date"
        ],
        errors="coerce",
    )

    jours_fr = {
        0: "Lundi",
        1: "Mardi",
        2: "Mercredi",
        3: "Jeudi",
        4: "Vendredi",
        5: "Samedi",
        6: "Dimanche",
    }

    # --------------------------------------------------------
    # VARIABLES CALENDRIER
    # --------------------------------------------------------

    daily[
        "annee"
    ] = (
        daily[
            "date"
        ].dt.year
    )

    daily[
        "mois"
    ] = (
        daily[
            "date"
        ].dt.month
    )

    daily[
        "jour_semaine"
    ] = (
        daily[
            "date"
        ]
        .dt.dayofweek
        .map(
            jours_fr
        )
    )

    daily[
        "mois_annee"
    ] = (
        daily[
            "date"
        ]
        .dt.to_period(
            "M"
        )
        .astype(str)
    )

    # --------------------------------------------------------
    # TRI
    # --------------------------------------------------------

    daily = (
        daily
        .sort_values(
            [
                "deviceId",
                "date",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return daily


# ============================================================
# RAVITAILLEMENTS POTENTIELS
# ============================================================

def build_fact_refueling_events(
    refueling_episodes: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prépare les épisodes de ravitaillement
    pour la plateforme.

    Cette version gère également
    le cas où aucun ravitaillement
    n'est détecté.
    """

    refuels = (
        refueling_episodes.copy()
    )

    # --------------------------------------------------------
    # GARANTIR LA STRUCTURE D'ENTREE
    # --------------------------------------------------------

    refuels = ensure_columns(
        refuels,
        [
            "refuel_episode_id",
            "deviceId",
            "start_time",
            "end_time",
            "duration_sec",
            "n_steps",
            "start_fuel_pct",
            "end_fuel_pct",
            "total_delta_fuel_pct",
            "max_speed_kmh",
            "mean_speed_kmh",
        ],
    )

    # --------------------------------------------------------
    # CAS : AUCUN RAVITAILLEMENT
    # --------------------------------------------------------

    if refuels.empty:

        return pd.DataFrame(
            columns=
                REFUEL_COLUMNS
        )

    # --------------------------------------------------------
    # DATES
    # --------------------------------------------------------

    refuels[
        "start_time"
    ] = pd.to_datetime(
        refuels[
            "start_time"
        ],
        errors="coerce",
    )

    refuels[
        "end_time"
    ] = pd.to_datetime(
        refuels[
            "end_time"
        ],
        errors="coerce",
    )

    # --------------------------------------------------------
    # IDENTIFIANT EVENEMENT
    # --------------------------------------------------------

    refuels[
        "event_id"
    ] = (
        refuels[
            "refuel_episode_id"
        ]
        .astype(str)
    )

    # --------------------------------------------------------
    # DATE PRINCIPALE EVENEMENT
    # --------------------------------------------------------

    refuels[
        "event_time"
    ] = (
        refuels[
            "start_time"
        ]
    )

    # --------------------------------------------------------
    # CATEGORIE
    # --------------------------------------------------------

    refuels[
        "event_category"
    ] = (
        "Ravitaillement potentiel"
    )

    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    refuels[
        "source_detection"
    ] = (
        "Règle métier"
    )

    # --------------------------------------------------------
    # VARIATION CARBURANT
    # --------------------------------------------------------

    refuels[
        "variation_fuel_pct"
    ] = (
        refuels[
            "total_delta_fuel_pct"
        ]
    )

    refuels[
        "fuel_level_pct"
    ] = (
        refuels[
            "end_fuel_pct"
        ]
    )

    # --------------------------------------------------------
    # GARANTIR LE SCHEMA FINAL
    # --------------------------------------------------------

    refuels = ensure_columns(
        refuels,
        REFUEL_COLUMNS,
    )

    # --------------------------------------------------------
    # TRI
    # --------------------------------------------------------

    refuels = (
        refuels
        .sort_values(
            [
                "deviceId",
                "event_time",
            ],
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )

    return (
        refuels[
            REFUEL_COLUMNS
        ]
    )


# ============================================================
# IDENTIFIANT UNIQUE DES ALERTES
# ============================================================

def create_alert_id(
    row: pd.Series,
) -> str:
    """
    Construit un identifiant stable
    pour chaque alerte.

    Les alertes issues des règles
    conservent leur suspicious_event_id.

    Les alertes IA uniquement reçoivent
    un identifiant basé sur le véhicule
    et l'horodatage.
    """

    suspicious_id = (
        row.get(
            "suspicious_event_id",
            np.nan,
        )
    )

    if pd.notna(
        suspicious_id
    ):

        return str(
            suspicious_id
        )

    fix_time = (
        row.get(
            "fixTime",
            np.nan,
        )
    )

    if pd.notna(
        fix_time
    ):

        timestamp = (
            pd.Timestamp(
                fix_time
            )
            .strftime(
                "%Y%m%d_%H%M%S_%f"
            )
        )

    else:

        timestamp = (
            f"LIGNE_{row.name:05d}"
        )

    device_id = (
        row.get(
            "deviceId",
            "NA",
        )
    )

    return (
        f"AI_{device_id}_"
        f"{timestamp}"
    )


# ============================================================
# PRIORISATION DES ALERTES
# ============================================================

def define_alert_priority(
    row: pd.Series,
) -> pd.Series:
    """
    Attribue une priorité explicable
    à chaque alerte.

    La priorité organise l'investigation.
    Elle ne confirme pas une anomalie réelle.
    """

    source = str(
        row.get(
            "source_detection",
            "",
        )
    )

    confidence = str(
        row.get(
            "confidence_level",
            "",
        )
    )

    temporal_context = str(
        row.get(
            "contexte_temporel",
            "",
        )
    )

    # --------------------------------------------------------
    # P1
    # --------------------------------------------------------

    if (
        source
        == "Règle + IA"
        and
        confidence
        == "Forte"
    ):

        return pd.Series(
            [
                1,
                "P1 - Critique",
                (
                    "Règle + IA avec "
                    "confiance forte."
                ),
            ]
        )

    # --------------------------------------------------------
    # P2
    # --------------------------------------------------------

    if (
        source
        == "Règle + IA"
        and
        confidence
        == "Moyenne"
    ):

        return pd.Series(
            [
                2,
                "P2 - Élevée",
                (
                    "Règle + IA avec "
                    "confiance moyenne."
                ),
            ]
        )

    # --------------------------------------------------------
    # P3 - REGLE + IA
    # --------------------------------------------------------

    if (
        source
        == "Règle + IA"
    ):

        return pd.Series(
            [
                3,
                "P3 - À investiguer",
                (
                    "Règle + IA mais confiance "
                    "faible ou non évaluée."
                ),
            ]
        )

    # --------------------------------------------------------
    # P4
    # --------------------------------------------------------

    if (
        source
        == "Règle uniquement"
    ):

        return pd.Series(
            [
                4,
                "P4 - Faible",
                (
                    "Alerte des règles non retenue "
                    "dans le percentile IA."
                ),
            ]
        )

    # --------------------------------------------------------
    # P5
    # --------------------------------------------------------

    if (
        "Coupure > 30 min"
        in temporal_context
    ):

        return pd.Series(
            [
                5,
                "P5 - Prudence",
                (
                    "Candidat IA observé après "
                    "une longue coupure de transmission."
                ),
            ]
        )

    # --------------------------------------------------------
    # P3 - IA UNIQUEMENT
    # --------------------------------------------------------

    return pd.Series(
        [
            3,
            "P3 - À investiguer",
            (
                "Candidat proposé uniquement par "
                "l'IA avec un intervalle exploitable."
            ),
        ]
    )


# ============================================================
# TABLE DES ALERTES
# ============================================================

def build_fact_fuel_alerts(
    ai_top_candidates: pd.DataFrame,
    rules_vs_ai_comparison: pd.DataFrame,
    suspicious_events_analyzed: pd.DataFrame,
) -> pd.DataFrame:
    """
    Fusionne :

    - les candidats IA ;
    - les événements règles + IA ;
    - les événements règle uniquement ;
    - l'analyse contextuelle.

    Cette version supporte également :

    - 0 candidat IA ;
    - 0 alerte règle ;
    - 0 recouvrement règle + IA ;
    - 0 alerte finale.
    """

    ai_alerts = (
        ai_top_candidates.copy()
    )

    rules_vs_ai = (
        rules_vs_ai_comparison.copy()
    )

    contextual = (
        suspicious_events_analyzed.copy()
    )

    # ========================================================
    # GARANTIR LES COLONNES DES CANDIDATS IA
    # ========================================================

    ai_alerts = ensure_columns(
        ai_alerts,
        [
            "deviceId",
            "fixTime",
            "suspicious_event_id",
            "fuelLevel",
            "drop_abs_pct",
            "delta_time_sec",
            "speed_kmh",
            "distance_abs_m",
            "ignition",
            "ai_anomaly_score",
            "ai_score_percentile",
            "contexte_temporel",
            "latitude",
            "longitude",
        ],
    )

    # ========================================================
    # GARANTIR LES COLONNES COMPARAISON REGLES / IA
    # ========================================================

    rules_vs_ai = ensure_columns(
        rules_vs_ai,
        [
            "deviceId",
            "fixTime",
            "suspicious_event_id",
            "fuelLevel",
            "drop_abs_pct",
            "delta_time_sec",
            "speed_kmh",
            "distance_abs_m",
            "ignition",
            "ai_anomaly_flag",
            "latitude",
            "longitude",
        ],
    )

    # ========================================================
    # DETAILS CONTEXTUELS
    # ========================================================

    contextual_columns = [
        "suspicious_event_id",
        "persistence",
        "context_support",
        "confidence_level",
        "analysis_reason",
        "fuel_before_pct",
        "fuel_event_pct",
        "recovery_ratio",
        "latitude",
        "longitude",
        "lien_carte",
    ]

    contextual = ensure_columns(
        contextual,
        contextual_columns,
    )

    # ========================================================
    # HARMONISER LES DATES
    # ========================================================

    for dataframe in [
        ai_alerts,
        rules_vs_ai,
        contextual,
    ]:

        if (
            "fixTime"
            in dataframe.columns
        ):

            dataframe[
                "fixTime"
            ] = pd.to_datetime(
                dataframe[
                    "fixTime"
                ],
                errors="coerce",
            )

    # ========================================================
    # DETAILS CONTEXTUELS UNIQUES
    # ========================================================

    contextual_details = (
        contextual[
            contextual_columns
        ]
        .drop_duplicates(
            subset=[
                "suspicious_event_id"
            ]
        )
    )

    # ========================================================
    # 1. CANDIDATS IA
    # ========================================================

    ai_alerts[
        "source_detection"
    ] = np.where(
        ai_alerts[
            "suspicious_event_id"
        ].notna(),
        "Règle + IA",
        "IA uniquement",
    )

    ai_alerts[
        "alert_type"
    ] = (
        "Baisse de carburant atypique"
    )

    ai_alerts[
        "detection_combinee"
    ] = (
        ai_alerts[
            "source_detection"
        ]
    )

    # Tous les éléments de ai_top_candidates
    # sont déjà les candidats sélectionnés
    # par Isolation Forest.

    ai_alerts[
        "ai_anomaly_flag"
    ] = True

    # --------------------------------------------------------
    # ENRICHISSEMENT CONTEXTUEL DES CANDIDATS IA
    # --------------------------------------------------------

    context_for_ai = (
        contextual_details[
            [
                "suspicious_event_id",
                "persistence",
                "context_support",
                "confidence_level",
                "analysis_reason",
                "fuel_before_pct",
                "fuel_event_pct",
                "recovery_ratio",
                "lien_carte",
            ]
        ]
    )

    ai_alerts = (
        ai_alerts
        .merge(
            context_for_ai,
            on="suspicious_event_id",
            how="left",
        )
    )

    # ========================================================
    # 2. ALERTES REGLES UNIQUEMENT
    # ========================================================

    rule_ai_flag = (
        convert_boolean_series(
            rules_vs_ai[
                "ai_anomaly_flag"
            ]
        )
    )

    rule_only = (
        rules_vs_ai.loc[
            ~rule_ai_flag
        ]
        .copy()
    )

    # --------------------------------------------------------
    # ENRICHISSEMENT CONTEXTUEL
    # --------------------------------------------------------

    if not rule_only.empty:

        rule_only = (
            rule_only
            .merge(
                contextual_details,
                on="suspicious_event_id",
                how="left",
                suffixes=(
                    "_rule",
                    "_context",
                ),
            )
        )

        # ----------------------------------------------------
        # COORDONNEES GPS
        # ----------------------------------------------------

        if (
            "latitude_rule"
            in rule_only.columns
        ):

            rule_only[
                "latitude"
            ] = (
                rule_only[
                    "latitude_rule"
                ]
                .combine_first(
                    rule_only[
                        "latitude_context"
                    ]
                )
            )

        elif (
            "latitude_context"
            in rule_only.columns
        ):

            rule_only[
                "latitude"
            ] = (
                rule_only[
                    "latitude_context"
                ]
            )

        if (
            "longitude_rule"
            in rule_only.columns
        ):

            rule_only[
                "longitude"
            ] = (
                rule_only[
                    "longitude_rule"
                ]
                .combine_first(
                    rule_only[
                        "longitude_context"
                    ]
                )
            )

        elif (
            "longitude_context"
            in rule_only.columns
        ):

            rule_only[
                "longitude"
            ] = (
                rule_only[
                    "longitude_context"
                ]
            )

        # ----------------------------------------------------
        # TYPE ET SOURCE
        # ----------------------------------------------------

        rule_only[
            "alert_type"
        ] = (
            "Baisse de carburant atypique"
        )

        rule_only[
            "source_detection"
        ] = (
            "Règle uniquement"
        )

        rule_only[
            "detection_combinee"
        ] = (
            "Règle uniquement"
        )

        rule_only[
            "ai_anomaly_flag"
        ] = False

        # ----------------------------------------------------
        # CONTEXTE TEMPOREL
        # ----------------------------------------------------

        rule_only[
            "contexte_temporel"
        ] = np.where(
            rule_only[
                "delta_time_sec"
            ] <= 1800,
            "Intervalle <= 30 min",
            (
                "Coupure > 30 min : "
                "interprétation prudente"
            ),
        )

    # ========================================================
    # 3. ALIGNER LES COLONNES
    # ========================================================

    base_alert_columns = [
        column
        for column
        in ALERT_COLUMNS
        if column not in [
            "alert_id",
            "rang_priorite",
            "priorite_alerte",
            "raison_priorite",
            "statut_validation",
        ]
    ]

    ai_alerts = ensure_columns(
        ai_alerts,
        base_alert_columns,
    )

    rule_only = ensure_columns(
        rule_only,
        base_alert_columns,
    )

    # ========================================================
    # 4. FUSION
    # ========================================================

    alerts = pd.concat(
        [
            ai_alerts[
                base_alert_columns
            ],
            rule_only[
                base_alert_columns
            ],
        ],
        ignore_index=True,
    )

    # ========================================================
    # CAS : AUCUNE ALERTE
    # ========================================================

    if alerts.empty:

        return pd.DataFrame(
            columns=
                ALERT_COLUMNS
        )

    # ========================================================
    # 5. IDENTIFIANTS UNIQUES
    # ========================================================

    alerts[
        "alert_id"
    ] = alerts.apply(
        create_alert_id,
        axis=1,
    )

    # ========================================================
    # 6. PRIORISATION
    # ========================================================

    priorities = (
        alerts.apply(
            define_alert_priority,
            axis=1,
        )
    )

    priorities.columns = [
        "rang_priorite",
        "priorite_alerte",
        "raison_priorite",
    ]

    alerts = pd.concat(
        [
            alerts,
            priorities,
        ],
        axis=1,
    )

    # ========================================================
    # 7. VALEURS POUR LA PLATEFORME
    # ========================================================

    alerts[
        "confidence_level"
    ] = (
        alerts[
            "confidence_level"
        ]
        .fillna(
            "Non évaluée"
        )
    )

    alerts[
        "persistence"
    ] = (
        alerts[
            "persistence"
        ]
        .fillna(
            "Non évaluée"
        )
    )

    alerts[
        "context_support"
    ] = (
        alerts[
            "context_support"
        ]
        .fillna(
            "Non évalué"
        )
    )

    alerts[
        "analysis_reason"
    ] = (
        alerts[
            "analysis_reason"
        ]
        .fillna(
            (
                "Événement proposé uniquement par "
                "Isolation Forest ; validation "
                "métier nécessaire."
            )
        )
    )

    alerts[
        "statut_validation"
    ] = (
        "À vérifier"
    )

    # ========================================================
    # 8. DEDOUBLONNAGE FINAL
    # ========================================================

    alerts = (
        alerts
        .drop_duplicates(
            subset=[
                "alert_id"
            ]
        )
        .sort_values(
            [
                "rang_priorite",
                "fixTime",
            ],
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )

    alerts = ensure_columns(
        alerts,
        ALERT_COLUMNS,
    )

    return (
        alerts[
            ALERT_COLUMNS
        ]
    )


# ============================================================
# TABLE UNIQUE DES EVENEMENTS CARBURANT
# ============================================================

def build_fact_fuel_events(
    fact_refueling_events: pd.DataFrame,
    fact_fuel_alerts: pd.DataFrame,
) -> pd.DataFrame:
    """
    Regroupe les ravitaillements
    et les alertes dans une table
    chronologique commune.

    Supporte :

    - 0 ravitaillement ;
    - 0 alerte ;
    - 0 événement du tout.
    """

    refuels = (
        fact_refueling_events.copy()
    )

    alerts = (
        fact_fuel_alerts.copy()
    )

    # ========================================================
    # GARANTIR LES COLONNES RAVITAILLEMENTS
    # ========================================================

    refuels = ensure_columns(
        refuels,
        [
            "event_id",
            "deviceId",
            "event_time",
            "event_category",
            "source_detection",
            "variation_fuel_pct",
            "fuel_level_pct",
        ],
    )

    # ========================================================
    # GARANTIR LES COLONNES ALERTES
    # ========================================================

    alerts = ensure_columns(
        alerts,
        [
            "alert_id",
            "deviceId",
            "fixTime",
            "alert_type",
            "source_detection",
            "priorite_alerte",
            "drop_abs_pct",
            "fuelLevel",
            "confidence_level",
            "ai_score_percentile",
            "latitude",
            "longitude",
            "lien_carte",
        ],
    )

    # ========================================================
    # TABLE DES RAVITAILLEMENTS
    # ========================================================

    if refuels.empty:

        refuel_events = (
            pd.DataFrame(
                columns=
                    FUEL_EVENT_COLUMNS
            )
        )

    else:

        refuel_events = pd.DataFrame(
            {
                "event_id":
                    refuels[
                        "event_id"
                    ],

                "deviceId":
                    refuels[
                        "deviceId"
                    ],

                "event_time":
                    refuels[
                        "event_time"
                    ],

                "event_category":
                    refuels[
                        "event_category"
                    ],

                "source_detection":
                    refuels[
                        "source_detection"
                    ],

                "priorite_alerte":
                    "Information",

                "variation_fuel_pct":
                    refuels[
                        "variation_fuel_pct"
                    ],

                "fuel_level_pct":
                    refuels[
                        "fuel_level_pct"
                    ],

                "confidence_level":
                    "Non applicable",

                "ai_score_percentile":
                    np.nan,

                "latitude":
                    np.nan,

                "longitude":
                    np.nan,

                "lien_carte":
                    np.nan,
            }
        )

    # ========================================================
    # TABLE DES ALERTES
    # ========================================================

    if alerts.empty:

        alert_events = (
            pd.DataFrame(
                columns=
                    FUEL_EVENT_COLUMNS
            )
        )

    else:

        alert_events = pd.DataFrame(
            {
                "event_id":
                    alerts[
                        "alert_id"
                    ],

                "deviceId":
                    alerts[
                        "deviceId"
                    ],

                "event_time":
                    alerts[
                        "fixTime"
                    ],

                "event_category":
                    alerts[
                        "alert_type"
                    ],

                "source_detection":
                    alerts[
                        "source_detection"
                    ],

                "priorite_alerte":
                    alerts[
                        "priorite_alerte"
                    ],

                "variation_fuel_pct":
                    -alerts[
                        "drop_abs_pct"
                    ],

                "fuel_level_pct":
                    alerts[
                        "fuelLevel"
                    ],

                "confidence_level":
                    alerts[
                        "confidence_level"
                    ],

                "ai_score_percentile":
                    alerts[
                        "ai_score_percentile"
                    ],

                "latitude":
                    alerts[
                        "latitude"
                    ],

                "longitude":
                    alerts[
                        "longitude"
                    ],

                "lien_carte":
                    alerts[
                        "lien_carte"
                    ],
            }
        )

    # ========================================================
    # FUSION
    # ========================================================

    events = pd.concat(
        [
            refuel_events,
            alert_events,
        ],
        ignore_index=True,
    )

    # ========================================================
    # CAS : AUCUN EVENEMENT
    # ========================================================

    if events.empty:

        return pd.DataFrame(
            columns=
                FUEL_EVENT_COLUMNS
        )

    # ========================================================
    # DATE
    # ========================================================

    events[
        "event_time"
    ] = pd.to_datetime(
        events[
            "event_time"
        ],
        errors="coerce",
    )

    # ========================================================
    # TRI CHRONOLOGIQUE
    # ========================================================

    events = (
        events
        .sort_values(
            [
                "deviceId",
                "event_time",
            ],
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )

    events = ensure_columns(
        events,
        FUEL_EVENT_COLUMNS,
    )

    return (
        events[
            FUEL_EVENT_COLUMNS
        ]
    )


# ============================================================
# RESUME GLOBAL DE LA PLATEFORME
# ============================================================

def build_fleet_summary(
    kpi_global: Dict,
    dim_vehicles: pd.DataFrame,
    fact_refueling_events: pd.DataFrame,
    fact_fuel_alerts: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construit la ligne de synthèse
    utilisée par le dashboard.
    """

    vehicles_for_summary = (
        ensure_columns(
            dim_vehicles,
            [
                "nb_alertes_regles",
                "nb_candidats_ia",
                "nb_overlap_regles_ia",
            ],
        )
    )

    alerts_for_summary = (
        ensure_columns(
            fact_fuel_alerts,
            [
                "rang_priorite",
            ],
        )
    )

    summary = pd.DataFrame(
        [
            {
                "date_generation":
                    pd.Timestamp.now(),

                "nombre_vehicules":
                    int(
                        kpi_global.get(
                            "nombre_vehicules",
                            len(
                                dim_vehicles
                            ),
                        )
                    ),

                "nombre_total_mesures":
                    int(
                        kpi_global.get(
                            "nombre_total_mesures",
                            0,
                        )
                    ),

                "distance_totale_km":
                    float(
                        kpi_global.get(
                            "distance_totale_km",
                            0.0,
                        )
                    ),

                "nb_ravitaillements_potentiels":
                    int(
                        len(
                            fact_refueling_events
                        )
                    ),

                "nb_alertes_regles":
                    int(
                        vehicles_for_summary[
                            "nb_alertes_regles"
                        ]
                        .fillna(0)
                        .sum()
                    ),

                "nb_candidats_ia":
                    int(
                        vehicles_for_summary[
                            "nb_candidats_ia"
                        ]
                        .fillna(0)
                        .sum()
                    ),

                "nb_regle_et_ia":
                    int(
                        vehicles_for_summary[
                            "nb_overlap_regles_ia"
                        ]
                        .fillna(0)
                        .sum()
                    ),

                "nb_alertes_finales_uniques":
                    int(
                        len(
                            fact_fuel_alerts
                        )
                    ),

                "nb_alertes_p1_critiques":
                    int(
                        (
                            alerts_for_summary[
                                "rang_priorite"
                            ]
                            == 1
                        )
                        .sum()
                    ),

                "nb_incoherences_fuel":
                    int(
                        kpi_global.get(
                            "nb_incoherences_fuel",
                            0,
                        )
                    ),
            }
        ]
    )

    return summary


# ============================================================
# CONTROLES DE QUALITE DES TABLES
# ============================================================

def validate_platform_tables(
    dim_vehicles: pd.DataFrame,
    fact_fleet_daily: pd.DataFrame,
    fact_refueling_events: pd.DataFrame,
    fact_fuel_alerts: pd.DataFrame,
    fact_fuel_events: pd.DataFrame,
) -> Dict:
    """
    Vérifie l'unicité des clés principales.

    La fonction supporte aussi
    les tables d'événements vides.
    """

    dim_check = (
        ensure_columns(
            dim_vehicles,
            [
                "deviceId",
            ],
        )
    )

    daily_check = (
        ensure_columns(
            fact_fleet_daily,
            [
                "deviceId",
                "date",
            ],
        )
    )

    refuel_check = (
        ensure_columns(
            fact_refueling_events,
            [
                "event_id",
            ],
        )
    )

    alerts_check = (
        ensure_columns(
            fact_fuel_alerts,
            [
                "alert_id",
            ],
        )
    )

    events_check = (
        ensure_columns(
            fact_fuel_events,
            [
                "event_id",
            ],
        )
    )

    controls = {

        "doublons_dim_vehicles":
            int(
                dim_check
                .duplicated(
                    subset=[
                        "deviceId"
                    ]
                )
                .sum()
            ),

        "doublons_fact_fleet_daily":
            int(
                daily_check
                .duplicated(
                    subset=[
                        "deviceId",
                        "date",
                    ]
                )
                .sum()
            ),

        "doublons_fact_refueling_events":
            int(
                refuel_check
                .duplicated(
                    subset=[
                        "event_id"
                    ]
                )
                .sum()
            ),

        "doublons_fact_fuel_alerts":
            int(
                alerts_check
                .duplicated(
                    subset=[
                        "alert_id"
                    ]
                )
                .sum()
            ),

        "doublons_fact_fuel_events":
            int(
                events_check
                .duplicated(
                    subset=[
                        "event_id"
                    ]
                )
                .sum()
            ),
    }

    controls[
        "nombre_total_problemes"
    ] = int(
        sum(
            controls.values()
        )
    )

    return controls


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def prepare_platform_tables(
    kpi_vehicle: pd.DataFrame,
    kpi_daily: pd.DataFrame,
    kpi_global: Dict,
    refueling_episodes: pd.DataFrame,
    suspicious_events_analyzed: pd.DataFrame,
    ai_top_candidates: pd.DataFrame,
    rules_vs_ai_comparison: pd.DataFrame,
    ai_vehicle_summary: pd.DataFrame,
) -> Dict:
    """
    Prépare toutes les tables finales
    utilisées par :

    - PostgreSQL ;
    - FastAPI ;
    - Next.js ;
    - le dashboard.

    La préparation reste valide même
    lorsque les tables d'événements
    sont vides.
    """

    # --------------------------------------------------------
    # 1. DIMENSION VEHICULES
    # --------------------------------------------------------

    dim_vehicles = (
        build_dim_vehicles(
            kpi_vehicle,
            ai_vehicle_summary,
        )
    )

    # --------------------------------------------------------
    # 2. KPI JOURNALIERS
    # --------------------------------------------------------

    fact_fleet_daily = (
        build_fact_fleet_daily(
            kpi_daily
        )
    )

    # --------------------------------------------------------
    # 3. RAVITAILLEMENTS POTENTIELS
    # --------------------------------------------------------

    fact_refueling_events = (
        build_fact_refueling_events(
            refueling_episodes
        )
    )

    # --------------------------------------------------------
    # 4. ALERTES FINALES
    # --------------------------------------------------------

    fact_fuel_alerts = (
        build_fact_fuel_alerts(
            ai_top_candidates,
            rules_vs_ai_comparison,
            suspicious_events_analyzed,
        )
    )

    # --------------------------------------------------------
    # 5. TOUS LES EVENEMENTS CARBURANT
    # --------------------------------------------------------

    fact_fuel_events = (
        build_fact_fuel_events(
            fact_refueling_events,
            fact_fuel_alerts,
        )
    )

    # --------------------------------------------------------
    # 6. RESUME GLOBAL
    # --------------------------------------------------------

    fleet_summary = (
        build_fleet_summary(
            kpi_global,
            dim_vehicles,
            fact_refueling_events,
            fact_fuel_alerts,
        )
    )

    # --------------------------------------------------------
    # 7. CONTROLES
    # --------------------------------------------------------

    controls = (
        validate_platform_tables(
            dim_vehicles,
            fact_fleet_daily,
            fact_refueling_events,
            fact_fuel_alerts,
            fact_fuel_events,
        )
    )

    # --------------------------------------------------------
    # TABLE ALERTES SECURISEE POUR LES COMPTAGES
    # --------------------------------------------------------

    alerts_for_summary = (
        ensure_columns(
            fact_fuel_alerts,
            [
                "rang_priorite",
            ],
        )
    )

    # --------------------------------------------------------
    # RESUME TECHNIQUE
    # --------------------------------------------------------

    summary = {

        "nombre_vehicules":
            int(
                len(
                    dim_vehicles
                )
            ),

        "nombre_kpi_journaliers":
            int(
                len(
                    fact_fleet_daily
                )
            ),

        "nombre_ravitaillements":
            int(
                len(
                    fact_refueling_events
                )
            ),

        "nombre_alertes_finales":
            int(
                len(
                    fact_fuel_alerts
                )
            ),

        "nombre_evenements_carburant":
            int(
                len(
                    fact_fuel_events
                )
            ),

        "nombre_alertes_p1":
            int(
                (
                    alerts_for_summary[
                        "rang_priorite"
                    ]
                    == 1
                )
                .sum()
            ),

        "nombre_alertes_p2":
            int(
                (
                    alerts_for_summary[
                        "rang_priorite"
                    ]
                    == 2
                )
                .sum()
            ),

        "nombre_alertes_p3":
            int(
                (
                    alerts_for_summary[
                        "rang_priorite"
                    ]
                    == 3
                )
                .sum()
            ),

        "nombre_alertes_p4":
            int(
                (
                    alerts_for_summary[
                        "rang_priorite"
                    ]
                    == 4
                )
                .sum()
            ),

        "nombre_alertes_p5":
            int(
                (
                    alerts_for_summary[
                        "rang_priorite"
                    ]
                    == 5
                )
                .sum()
            ),
    }

    # --------------------------------------------------------
    # RESULTAT
    # --------------------------------------------------------

    return {

        "dim_vehicles":
            dim_vehicles,

        "fact_fleet_daily":
            fact_fleet_daily,

        "fact_refueling_events":
            fact_refueling_events,

        "fact_fuel_alerts":
            fact_fuel_alerts,

        "fact_fuel_events":
            fact_fuel_events,

        "fleet_summary":
            fleet_summary,

        "controls":
            controls,

        "summary":
            summary,
    }