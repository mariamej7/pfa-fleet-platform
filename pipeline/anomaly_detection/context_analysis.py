from typing import Dict

import numpy as np
import pandas as pd


# ============================================================
# PARAMETRES
# ============================================================

# Le Notebook 3 analyse 30 minutes avant
# et 30 minutes apres chaque baisse suspecte.
FENETRE_CONTEXTE_MIN = 30


# Colonnes produites par l'analyse contextuelle.
# Elles sont aussi conservees lorsque le dataset
# ne contient aucune baisse suspecte.
ANALYZED_COLUMNS = [
    "suspicious_event_id",
    "deviceId",
    "fixTime",
    "fuel_before_pct",
    "fuel_event_pct",
    "drop_abs_pct",
    "delta_time_sec",
    "drop_rate_pct_per_min",
    "speed_kmh",
    "distance_abs_m",
    "ignition",
    "latitude",
    "longitude",
    "gps_distance_prev_m",
    "n_before_30min",
    "n_after_30min",
    "first_after_time",
    "first_after_fuel_pct",
    "gap_to_first_after_sec",
    "median_after_30min_pct",
    "last_after_30min_pct",
    "recovery_ratio",
    "persistence",
    "context_support",
    "confidence_level",
    "analysis_reason",
    "lien_carte",
]


# ============================================================
# DISTANCE GPS
# ============================================================

def haversine_m(
    lat1,
    lon1,
    lat2,
    lon2,
):
    """
    Calcule la distance approximative en metres
    entre deux positions GPS.
    """

    values = [
        lat1,
        lon1,
        lat2,
        lon2,
    ]

    if any(
        pd.isna(value)
        for value in values
    ):
        return np.nan

    earth_radius_m = 6371000.0

    lat1_rad = np.radians(
        lat1
    )

    lat2_rad = np.radians(
        lat2
    )

    delta_lat = np.radians(
        lat2 - lat1
    )

    delta_lon = np.radians(
        lon2 - lon1
    )

    a = (
        np.sin(
            delta_lat / 2
        ) ** 2
        +
        np.cos(
            lat1_rad
        )
        * np.cos(
            lat2_rad
        )
        * np.sin(
            delta_lon / 2
        ) ** 2
    )

    return float(
        2
        * earth_radius_m
        * np.arcsin(
            np.sqrt(a)
        )
    )


# ============================================================
# PREPARATION DES DONNEES
# ============================================================

def prepare_context_data(
    df_rules: pd.DataFrame,
    suspicious_events: pd.DataFrame,
) -> Dict:
    """
    Prepare les donnees utilisees pour analyser
    le contexte autour des baisses suspectes.
    """

    df_context = (
        df_rules.copy()
    )

    events = (
        suspicious_events.copy()
    )

    # --------------------------------------------------------
    # Verification minimale du dataset principal
    # --------------------------------------------------------

    if (
        "fixTime"
        not in df_context.columns
    ):
        raise ValueError(
            (
                "La colonne fixTime est absente "
                "du dataset utilise pour "
                "l'analyse contextuelle."
            )
        )

    # --------------------------------------------------------
    # Dates du dataset principal
    # --------------------------------------------------------

    df_context[
        "fixTime"
    ] = pd.to_datetime(
        df_context[
            "fixTime"
        ].astype(str),
        format="mixed",
        errors="coerce",
    )

    # --------------------------------------------------------
    # Dates des evenements
    # --------------------------------------------------------

    if (
        "fixTime"
        in events.columns
    ):

        events[
            "fixTime"
        ] = pd.to_datetime(
            events[
                "fixTime"
            ].astype(str),
            format="mixed",
            errors="coerce",
        )

    elif events.empty:

        # Cas robuste :
        # aucun evenement et aucun schema fourni.
        events[
            "fixTime"
        ] = pd.Series(
            dtype="datetime64[ns]"
        )

    else:

        raise ValueError(
            (
                "La colonne fixTime est absente "
                "des evenements suspects."
            )
        )

    # --------------------------------------------------------
    # Colonnes numeriques
    # --------------------------------------------------------

    numeric_columns = [
        "fuelLevel",
        "speed_kmh",
        "latitude",
        "longitude",
        "delta_odometer_m",
    ]

    for column in numeric_columns:

        if (
            column
            in df_context.columns
        ):

            df_context[
                column
            ] = pd.to_numeric(
                df_context[
                    column
                ],
                errors="coerce",
            )

    # --------------------------------------------------------
    # Tri chronologique
    # --------------------------------------------------------

    df_context = (
        df_context
        .sort_values(
            [
                "deviceId",
                "fixTime",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return {
        "df_context":
            df_context,

        "suspicious_events":
            events,

        "invalid_dates_dataset":
            int(
                df_context[
                    "fixTime"
                ]
                .isna()
                .sum()
            ),

        "invalid_dates_events":
            int(
                events[
                    "fixTime"
                ]
                .isna()
                .sum()
            ),
    }


# ============================================================
# ANALYSE D'UN EVENEMENT
# ============================================================

def analyze_one_event(
    event: pd.Series,
    df_context: pd.DataFrame,
):
    """
    Analyse une baisse suspecte dans une fenetre
    de 30 minutes avant et apres l'evenement.
    """

    event_id = event[
        "suspicious_event_id"
    ]

    device_id = event[
        "deviceId"
    ]

    event_time = event[
        "fixTime"
    ]

    # --------------------------------------------------------
    # Fenetre temporelle
    # --------------------------------------------------------

    window_start = (
        event_time
        - pd.Timedelta(
            minutes=
                FENETRE_CONTEXTE_MIN
        )
    )

    window_end = (
        event_time
        + pd.Timedelta(
            minutes=
                FENETRE_CONTEXTE_MIN
        )
    )

    device_data = (
        df_context[
            df_context[
                "deviceId"
            ] == device_id
        ]
    )

    context = (
        device_data[
            (
                device_data[
                    "fixTime"
                ] >= window_start
            )
            &
            (
                device_data[
                    "fixTime"
                ] <= window_end
            )
        ]
        .copy()
    )

    # --------------------------------------------------------
    # Informations de contexte
    # --------------------------------------------------------

    context[
        "suspicious_event_id_context"
    ] = event_id

    context[
        "relative_time_sec"
    ] = (
        context[
            "fixTime"
        ]
        - event_time
    ).dt.total_seconds()

    context[
        "context_position"
    ] = np.select(
        [
            (
                context[
                    "relative_time_sec"
                ] < 0
            ),
            (
                context[
                    "relative_time_sec"
                ] == 0
            ),
        ],
        [
            "Avant",
            "Evenement",
        ],
        default="Apres",
    )

    # --------------------------------------------------------
    # Avant / apres
    # --------------------------------------------------------

    before = (
        context[
            context[
                "fixTime"
            ] < event_time
        ]
        .copy()
    )

    after = (
        context[
            context[
                "fixTime"
            ] > event_time
        ]
        .copy()
    )

    # On ignore les fuelLevel hors 0-100 %
    # pour valider la persistance.

    before_valid = (
        before[
            before[
                "fuelLevel"
            ].between(
                0,
                100,
            )
        ]
        .copy()
    )

    after_valid = (
        after[
            after[
                "fuelLevel"
            ].between(
                0,
                100,
            )
        ]
        .copy()
    )

    # --------------------------------------------------------
    # Niveau au moment de l'evenement
    # --------------------------------------------------------

    fuel_event = float(
        event[
            "fuelLevel"
        ]
    )

    drop_abs = float(
        event[
            "drop_abs_pct"
        ]
    )

    # Niveau estime juste avant la baisse.

    fuel_before = (
        fuel_event
        + drop_abs
    )

    # --------------------------------------------------------
    # Valeurs apres l'evenement
    # --------------------------------------------------------

    first_after_time = (
        pd.NaT
    )

    first_after_fuel = (
        np.nan
    )

    gap_after_sec = (
        np.nan
    )

    median_after = (
        np.nan
    )

    last_after = (
        np.nan
    )

    if (
        len(
            after_valid
        ) > 0
    ):

        after_valid = (
            after_valid
            .sort_values(
                "fixTime"
            )
        )

        first_after = (
            after_valid.iloc[0]
        )

        first_after_time = (
            first_after[
                "fixTime"
            ]
        )

        first_after_fuel = float(
            first_after[
                "fuelLevel"
            ]
        )

        gap_after_sec = (
            first_after_time
            - event_time
        ).total_seconds()

        median_after = float(
            after_valid[
                "fuelLevel"
            ].median()
        )

        last_after = float(
            after_valid.iloc[-1][
                "fuelLevel"
            ]
        )

    # ========================================================
    # RECOVERY RATIO
    # ========================================================

    if (
        len(
            after_valid
        ) == 0
        or drop_abs <= 0
    ):

        recovery_ratio = (
            np.nan
        )

    else:

        recovery_ratio = (
            median_after
            - fuel_event
        ) / drop_abs

    # ========================================================
    # QUALITE DU CONTEXTE
    # ========================================================

    if (
        len(
            after_valid
        ) == 0
    ):

        context_support = (
            "Absent"
        )

    elif (
        len(
            after_valid
        ) >= 2
        or gap_after_sec <= 600
    ):

        context_support = (
            "Suffisant"
        )

    else:

        context_support = (
            "Limite"
        )

    # ========================================================
    # PERSISTANCE + NIVEAU DE CONFIANCE
    # ========================================================

    if (
        len(
            after_valid
        ) == 0
    ):

        persistence = (
            "Non verifiable"
        )

        confidence_level = (
            "Indeterminee"
        )

        analysis_reason = (
            "Aucune mesure valide n'est disponible "
            "dans les 30 minutes apres la baisse."
        )

    elif (
        recovery_ratio >= 0.75
    ):

        persistence = (
            "Retour proche du niveau initial"
        )

        confidence_level = (
            "Faible"
        )

        analysis_reason = (
            "Le niveau remonte fortement vers le "
            "niveau observe avant la baisse. "
            "Un rebond ou une instabilite du "
            "capteur est possible."
        )

    elif (
        recovery_ratio <= 0.25
    ):

        persistence = (
            "Baisse persistante"
        )

        if (
            context_support
            == "Suffisant"
        ):

            confidence_level = (
                "Forte"
            )

            analysis_reason = (
                "La baisse reste visible apres "
                "l'evenement et le contexte apres "
                "la baisse est suffisamment renseigne."
            )

        else:

            confidence_level = (
                "Moyenne"
            )

            analysis_reason = (
                "La baisse semble persister, "
                "mais le contexte disponible apres "
                "l'evenement est limite."
            )

    else:

        persistence = (
            "Persistance partielle"
        )

        confidence_level = (
            "Moyenne"
        )

        analysis_reason = (
            "Le niveau recupere partiellement "
            "apres la baisse. L'evenement reste "
            "atypique mais son interpretation "
            "est moins certaine."
        )

    # ========================================================
    # DISTANCE GPS AVEC LA MESURE PRECEDENTE
    # ========================================================

    gps_distance_prev_m = (
        np.nan
    )

    if (
        len(
            before
        ) > 0
    ):

        previous_measurement = (
            before
            .sort_values(
                "fixTime"
            )
            .iloc[-1]
        )

        gps_distance_prev_m = (
            haversine_m(
                previous_measurement[
                    "latitude"
                ],
                previous_measurement[
                    "longitude"
                ],
                event[
                    "latitude"
                ],
                event[
                    "longitude"
                ],
            )
        )

    # ========================================================
    # RESULTAT
    # ========================================================

    result = {
        "suspicious_event_id":
            event_id,

        "deviceId":
            device_id,

        "fixTime":
            event_time,

        "fuel_before_pct":
            fuel_before,

        "fuel_event_pct":
            fuel_event,

        "drop_abs_pct":
            drop_abs,

        "delta_time_sec":
            event[
                "delta_time_sec"
            ],

        "drop_rate_pct_per_min":
            event[
                "drop_rate_pct_per_min"
            ],

        "speed_kmh":
            event[
                "speed_kmh"
            ],

        "distance_abs_m":
            event[
                "distance_abs_m"
            ],

        "ignition":
            event[
                "ignition"
            ],

        "latitude":
            event[
                "latitude"
            ],

        "longitude":
            event[
                "longitude"
            ],

        "gps_distance_prev_m":
            gps_distance_prev_m,

        "n_before_30min":
            int(
                len(
                    before_valid
                )
            ),

        "n_after_30min":
            int(
                len(
                    after_valid
                )
            ),

        "first_after_time":
            first_after_time,

        "first_after_fuel_pct":
            first_after_fuel,

        "gap_to_first_after_sec":
            gap_after_sec,

        "median_after_30min_pct":
            median_after,

        "last_after_30min_pct":
            last_after,

        "recovery_ratio":
            recovery_ratio,

        "persistence":
            persistence,

        "context_support":
            context_support,

        "confidence_level":
            confidence_level,

        "analysis_reason":
            analysis_reason,
    }

    return (
        result,
        context,
    )


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def analyze_suspicious_context(
    df_rules: pd.DataFrame,
    suspicious_events: pd.DataFrame,
) -> Dict:
    """
    Analyse automatiquement toutes les baisses
    suspectes detectees par les regles.
    """

    preparation = (
        prepare_context_data(
            df_rules,
            suspicious_events,
        )
    )

    df_context = (
        preparation[
            "df_context"
        ]
    )

    events = (
        preparation[
            "suspicious_events"
        ]
    )

    results = []
    event_contexts = []

    # --------------------------------------------------------
    # Aucun evenement
    # --------------------------------------------------------

    if events.empty:

        # ----------------------------------------------------
        # Tableau d'analyse vide mais avec le schema attendu.
        # ----------------------------------------------------

        suspicious_events_analyzed = (
            pd.DataFrame(
                columns=
                    ANALYZED_COLUMNS
            )
        )

        # ----------------------------------------------------
        # Tableau de contexte vide mais avec le schema
        # du dataset principal.
        # ----------------------------------------------------

        suspicious_events_context_30min = (
            df_context
            .iloc[0:0]
            .copy()
        )

        suspicious_events_context_30min[
            "suspicious_event_id_context"
        ] = pd.Series(
            dtype="object"
        )

        suspicious_events_context_30min[
            "relative_time_sec"
        ] = pd.Series(
            dtype="float64"
        )

        suspicious_events_context_30min[
            "context_position"
        ] = pd.Series(
            dtype="object"
        )

        # ----------------------------------------------------
        # Resumes vides mais structures.
        # ----------------------------------------------------

        confidence_summary = (
            pd.DataFrame(
                columns=[
                    "confidence_level",
                    "nombre_evenements",
                ]
            )
        )

        persistence_summary = (
            pd.DataFrame(
                columns=[
                    "persistence",
                    "nombre_evenements",
                ]
            )
        )

        return {
            "suspicious_events_analyzed":
                suspicious_events_analyzed,

            "suspicious_events_context_30min":
                suspicious_events_context_30min,

            "confidence_summary":
                confidence_summary,

            "persistence_summary":
                persistence_summary,

            "summary": {
                "nombre_evenements_analyses":
                    0,

                "nombre_lignes_contexte":
                    0,

                "dates_invalides_dataset":
                    preparation[
                        "invalid_dates_dataset"
                    ],

                "dates_invalides_evenements":
                    preparation[
                        "invalid_dates_events"
                    ],

                "nombre_confiance_forte":
                    0,

                "nombre_confiance_moyenne":
                    0,

                "nombre_confiance_faible":
                    0,

                "nombre_confiance_indeterminee":
                    0,
            },
        }

    # --------------------------------------------------------
    # Analyse evenement par evenement
    # --------------------------------------------------------

    for _, event in (
        events
        .sort_values(
            [
                "deviceId",
                "fixTime",
            ]
        )
        .iterrows()
    ):

        result, context = (
            analyze_one_event(
                event,
                df_context,
            )
        )

        results.append(
            result
        )

        event_contexts.append(
            context
        )

    suspicious_events_analyzed = (
        pd.DataFrame(
            results
        )
    )

    suspicious_events_context_30min = (
        pd.concat(
            event_contexts,
            ignore_index=True,
        )
    )

    # ========================================================
    # LIEN CARTOGRAPHIQUE
    # ========================================================

    suspicious_events_analyzed[
        "lien_carte"
    ] = (
        "https://www.google.com/maps?q="
        + suspicious_events_analyzed[
            "latitude"
        ].astype(str)
        + ","
        + suspicious_events_analyzed[
            "longitude"
        ].astype(str)
    )

    # ========================================================
    # RESUME PAR NIVEAU DE CONFIANCE
    # ========================================================

    confidence_summary = (
        suspicious_events_analyzed[
            "confidence_level"
        ]
        .value_counts(
            dropna=False
        )
        .rename_axis(
            "confidence_level"
        )
        .reset_index(
            name="nombre_evenements"
        )
    )

    # ========================================================
    # RESUME DE LA PERSISTANCE
    # ========================================================

    persistence_summary = (
        suspicious_events_analyzed[
            "persistence"
        ]
        .value_counts(
            dropna=False
        )
        .rename_axis(
            "persistence"
        )
        .reset_index(
            name="nombre_evenements"
        )
    )

    # ========================================================
    # RESUME GLOBAL
    # ========================================================

    summary = {
        "nombre_evenements_analyses":
            int(
                len(
                    suspicious_events_analyzed
                )
            ),

        "nombre_lignes_contexte":
            int(
                len(
                    suspicious_events_context_30min
                )
            ),

        "dates_invalides_dataset":
            preparation[
                "invalid_dates_dataset"
            ],

        "dates_invalides_evenements":
            preparation[
                "invalid_dates_events"
            ],

        "nombre_confiance_forte":
            int(
                (
                    suspicious_events_analyzed[
                        "confidence_level"
                    ]
                    == "Forte"
                ).sum()
            ),

        "nombre_confiance_moyenne":
            int(
                (
                    suspicious_events_analyzed[
                        "confidence_level"
                    ]
                    == "Moyenne"
                ).sum()
            ),

        "nombre_confiance_faible":
            int(
                (
                    suspicious_events_analyzed[
                        "confidence_level"
                    ]
                    == "Faible"
                ).sum()
            ),

        "nombre_confiance_indeterminee":
            int(
                (
                    suspicious_events_analyzed[
                        "confidence_level"
                    ]
                    == "Indeterminee"
                ).sum()
            ),
    }

    return {
        "suspicious_events_analyzed":
            suspicious_events_analyzed,

        "suspicious_events_context_30min":
            suspicious_events_context_30min,

        "confidence_summary":
            confidence_summary,

        "persistence_summary":
            persistence_summary,

        "summary":
            summary,
    }