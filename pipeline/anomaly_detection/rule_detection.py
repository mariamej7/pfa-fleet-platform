from typing import Dict, Optional

import numpy as np
import pandas as pd


# ============================================================
# PARAMETRES DES REGLES
# ============================================================

# Quantile utilise dans le Notebook 1.
Q_SEUIL = 0.995

# Variation maximale d'odometre pour considerer
# qu'un vehicule est probablement proche de l'arret.
SEUIL_DISTANCE_M = 100

# Une variation est consideree rapide
# si elle se produit en 30 minutes ou moins.
SEUIL_TEMPS_RAPIDE_SEC = 30 * 60

# Deux fortes hausses separees de 10 minutes
# ou moins sont regroupees dans le meme
# episode de ravitaillement potentiel.
MAX_GAP_REFUEL_SEC = 10 * 60


# ============================================================
# COLONNES DES TABLES EVENEMENTS
# ============================================================

REFUEL_EPISODE_COLUMNS = [
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
]


SUSPICIOUS_EVENT_COLUMNS = [
    "suspicious_event_id",
    "deviceId",
    "fixTime",
    "fuelLevel",
    "delta_fuel",
    "drop_abs_pct",
    "delta_time_sec",
    "drop_rate_pct_per_min",
    "speed_kmh",
    "distance_abs_m",
    "ignition",
    "latitude",
    "longitude",
    "event_reason",
]


# ============================================================
# POPULATION DE REFERENCE
# ============================================================

def build_reference_population(
    df: pd.DataFrame,
) -> Dict:
    """
    Construit automatiquement la population utilisee
    pour calculer les seuils statistiques.

    Les vehicules ayant au moins une valeur fuelLevel
    hors de 0-100 % sont exclus du calcul des seuils.

    Ils restent neanmoins presents dans le dataset
    et peuvent etre analyses sur leurs lignes valides.
    """

    fuel_hors_plage = (
        (df["fuelLevel"] < 0)
        |
        (df["fuelLevel"] > 100)
    )

    vehicles_with_quality_issue = (
        df.loc[
            fuel_hors_plage,
            "deviceId",
        ]
        .dropna()
        .unique()
        .tolist()
    )

    reference = (
        df[
            (
                ~df[
                    "deviceId"
                ].isin(
                    vehicles_with_quality_issue
                )
            )
            &
            (
                df[
                    "delta_fuel"
                ].notna()
            )
            &
            (
                ~df[
                    "flag_incoherence_fuel"
                ]
            )
        ]
        .copy()
    )

    # --------------------------------------------------------
    # Securite :
    # si tous les vehicules ont un probleme qualite,
    # on utilise toutes les transitions coherentes.
    # --------------------------------------------------------

    if reference.empty:

        reference = (
            df[
                (
                    df[
                        "delta_fuel"
                    ].notna()
                )
                &
                (
                    ~df[
                        "flag_incoherence_fuel"
                    ]
                )
            ]
            .copy()
        )

    return {
        "reference":
            reference,

        "vehicles_excluded_from_thresholds":
            vehicles_with_quality_issue,
    }


# ============================================================
# CALCUL DES SEUILS
# ============================================================

def compute_rule_thresholds(
    df: pd.DataFrame,
) -> Dict:
    """
    Calcule les seuils de hausse et de baisse
    a partir du quantile 99,5 %.

    Si aucune hausse ou aucune baisse exploitable
    n'existe, le seuil correspondant est None.

    Le pipeline continue alors normalement
    sans inventer de seuil artificiel.
    """

    reference_result = (
        build_reference_population(
            df
        )
    )

    reference = (
        reference_result[
            "reference"
        ]
    )

    # --------------------------------------------------------
    # Variations positives
    # --------------------------------------------------------

    variations_positives = (
        reference.loc[
            (
                reference[
                    "delta_fuel"
                ] > 0
            ),
            "delta_fuel",
        ]
        .dropna()
    )

    # --------------------------------------------------------
    # Variations negatives
    # --------------------------------------------------------

    variations_negatives_abs = (
        reference.loc[
            (
                reference[
                    "delta_fuel"
                ] < 0
            ),
            "delta_fuel",
        ]
        .abs()
        .dropna()
    )

    # --------------------------------------------------------
    # Seuil de ravitaillement
    # --------------------------------------------------------

    if variations_positives.empty:

        seuil_ravitaillement = None

    else:

        seuil_ravitaillement = float(
            variations_positives.quantile(
                Q_SEUIL
            )
        )

    # --------------------------------------------------------
    # Seuil de baisse forte
    # --------------------------------------------------------

    if variations_negatives_abs.empty:

        seuil_baisse_forte = None

    else:

        seuil_baisse_forte = float(
            variations_negatives_abs.quantile(
                Q_SEUIL
            )
        )

    return {
        "q_seuil":
            Q_SEUIL,

        "seuil_ravitaillement":
            seuil_ravitaillement,

        "seuil_baisse_forte":
            seuil_baisse_forte,

        "seuil_ravitaillement_disponible":
            (
                seuil_ravitaillement
                is not None
            ),

        "seuil_baisse_forte_disponible":
            (
                seuil_baisse_forte
                is not None
            ),

        "nombre_variations_positives_reference":
            int(
                len(
                    variations_positives
                )
            ),

        "nombre_variations_negatives_reference":
            int(
                len(
                    variations_negatives_abs
                )
            ),

        "vehicles_excluded_from_thresholds":
            reference_result[
                "vehicles_excluded_from_thresholds"
            ],

        "nombre_lignes_reference":
            int(
                len(
                    reference
                )
            ),
    }


# ============================================================
# VARIABLES DE CONTEXTE
# ============================================================

def add_rule_context(
    df: pd.DataFrame,
    seuil_ravitaillement: Optional[float],
) -> Dict:
    """
    Ajoute les indicateurs utilises par les regles :
    mouvement, arret probable, ignition et temps.
    """

    df_rules = (
        df.copy()
    )

    # --------------------------------------------------------
    # Candidats de forte hausse
    # --------------------------------------------------------

    if (
        seuil_ravitaillement
        is None
    ):

        # Aucun seuil possible car aucune hausse
        # exploitable n'existe dans le dataset.

        candidats_hausse = (
            df_rules
            .iloc[0:0]
            .copy()
        )

    else:

        candidats_hausse = (
            df_rules[
                (
                    ~df_rules[
                        "flag_incoherence_fuel"
                    ]
                )
                &
                (
                    df_rules[
                        "delta_fuel"
                    ]
                    > seuil_ravitaillement
                )
            ]
            .copy()
        )

    # --------------------------------------------------------
    # Seuil de vitesse proche de l'arret
    # --------------------------------------------------------

    if not candidats_hausse.empty:

        vitesse_candidate = (
            pd.to_numeric(
                candidats_hausse[
                    "speed_kmh"
                ],
                errors="coerce",
            )
            .dropna()
        )

        if vitesse_candidate.empty:

            seuil_vitesse_arret_kmh = (
                10.0
            )

        else:

            seuil_vitesse_arret_kmh = float(
                vitesse_candidate.quantile(
                    0.95
                )
            )

    else:

        # Valeur de securite deja utilisee
        # dans la logique du Notebook 1.
        seuil_vitesse_arret_kmh = (
            10.0
        )

    # --------------------------------------------------------
    # Mouvement significatif
    # --------------------------------------------------------

    df_rules[
        "mouvement_significatif"
    ] = (
        (
            df_rules[
                "speed_kmh"
            ]
            > seuil_vitesse_arret_kmh
        )
        |
        (
            df_rules[
                "delta_odometer_m"
            ]
            .abs()
            > SEUIL_DISTANCE_M
        )
    )

    # --------------------------------------------------------
    # Arret probable
    # --------------------------------------------------------

    df_rules[
        "arret_probable"
    ] = (
        (
            df_rules[
                "speed_kmh"
            ]
            <= seuil_vitesse_arret_kmh
        )
        &
        (
            df_rules[
                "delta_odometer_m"
            ]
            .abs()
            <= SEUIL_DISTANCE_M
        )
    )

    # --------------------------------------------------------
    # Ignition OFF
    # --------------------------------------------------------

    df_rules[
        "ignition_off_support"
    ] = (
        df_rules[
            "ignition"
        ]
        == False
    )

    # --------------------------------------------------------
    # Variation rapide
    # --------------------------------------------------------

    df_rules[
        "variation_rapide"
    ] = (
        df_rules[
            "delta_time_sec"
        ]
        <= SEUIL_TEMPS_RAPIDE_SEC
    )

    return {
        "df_rules":
            df_rules,

        "seuil_vitesse_arret_kmh":
            seuil_vitesse_arret_kmh,
    }


# ============================================================
# CLASSIFICATION DES VARIATIONS
# ============================================================

def classify_fuel_events(
    df: pd.DataFrame,
    seuil_ravitaillement: Optional[float],
    seuil_baisse_forte: Optional[float],
) -> pd.DataFrame:
    """
    Applique les regles du Notebook 1.

    Priorite :
    1. incoherence de mesure
    2. ravitaillement potentiel
    3. baisse suspecte
    4. consommation normale

    Un seuil None signifie simplement qu'aucune
    variation correspondante n'existe dans le dataset.
    """

    df_rules = (
        df.copy()
    )

    # --------------------------------------------------------
    # Incoherences
    # --------------------------------------------------------

    condition_incoherence = (
        df_rules[
            "flag_incoherence_fuel"
        ]
        .fillna(False)
        .astype(bool)
    )

    # --------------------------------------------------------
    # Ravitaillement
    # --------------------------------------------------------

    if (
        seuil_ravitaillement
        is None
    ):

        condition_ravitaillement = (
            pd.Series(
                False,
                index=df_rules.index,
                dtype=bool,
            )
        )

    else:

        condition_ravitaillement = (
            (~condition_incoherence)
            &
            (
                df_rules[
                    "delta_fuel"
                ]
                > seuil_ravitaillement
            )
        )

    # --------------------------------------------------------
    # Baisse suspecte
    # --------------------------------------------------------

    if (
        seuil_baisse_forte
        is None
    ):

        condition_baisse_suspecte = (
            pd.Series(
                False,
                index=df_rules.index,
                dtype=bool,
            )
        )

    else:

        condition_baisse_suspecte = (
            (~condition_incoherence)
            &
            (~condition_ravitaillement)
            &
            (
                df_rules[
                    "delta_fuel"
                ]
                < -seuil_baisse_forte
            )
            &
            (
                df_rules[
                    "variation_rapide"
                ]
            )
            &
            (
                df_rules[
                    "arret_probable"
                ]
            )
        )

    # --------------------------------------------------------
    # Type d'evenement
    # --------------------------------------------------------

    df_rules[
        "event_type"
    ] = np.select(
        [
            condition_incoherence,
            condition_ravitaillement,
            condition_baisse_suspecte,
        ],
        [
            "Incohérence de mesure",
            "Ravitaillement potentiel",
            "Baisse suspecte / anomalie potentielle",
        ],
        default=
            "Consommation normale",
    )

    # Premiere mesure de chaque vehicule :
    # aucune variation precedente a analyser.

    df_rules.loc[
        (
            df_rules[
                "delta_fuel"
            ].isna()
        ),
        "event_type",
    ] = pd.NA

    # --------------------------------------------------------
    # Explication par defaut
    # --------------------------------------------------------

    df_rules[
        "event_reason"
    ] = (
        "Variation non signalée par "
        "les règles de niveau 1"
    )

    # --------------------------------------------------------
    # Incoherence
    # --------------------------------------------------------

    df_rules.loc[
        condition_incoherence,
        "event_reason",
    ] = (
        "Valeur actuelle ou précédente de "
        "fuelLevel hors de la plage 0-100 %"
    )

    # --------------------------------------------------------
    # Ravitaillement proche de l'arret
    # --------------------------------------------------------

    df_rules.loc[
        (
            condition_ravitaillement
            &
            df_rules[
                "arret_probable"
            ]
        ),
        "event_reason",
    ] = (
        "Hausse extrême de fuelLevel + "
        "véhicule proche de l'arrêt"
    )

    # --------------------------------------------------------
    # Ravitaillement en mouvement
    # --------------------------------------------------------

    df_rules.loc[
        (
            condition_ravitaillement
            &
            (
                ~df_rules[
                    "arret_probable"
                ]
            )
        ),
        "event_reason",
    ] = (
        "Hausse extrême de fuelLevel ; "
        "contexte mouvement à vérifier"
    )

    # --------------------------------------------------------
    # Baisse suspecte avec ignition OFF
    # --------------------------------------------------------

    df_rules.loc[
        (
            condition_baisse_suspecte
            &
            df_rules[
                "ignition_off_support"
            ]
        ),
        "event_reason",
    ] = (
        "Baisse extrême et rapide + "
        "véhicule immobile + "
        "ignition=False en support"
    )

    # --------------------------------------------------------
    # Baisse suspecte sans ignition OFF
    # --------------------------------------------------------

    df_rules.loc[
        (
            condition_baisse_suspecte
            &
            (
                ~df_rules[
                    "ignition_off_support"
                ]
            )
        ),
        "event_reason",
    ] = (
        "Baisse extrême et rapide + "
        "véhicule immobile selon "
        "vitesse/odomètre"
    )

    # --------------------------------------------------------
    # Premiere mesure
    # --------------------------------------------------------

    df_rules.loc[
        (
            df_rules[
                "delta_fuel"
            ].isna()
        ),
        "event_reason",
    ] = pd.NA

    return df_rules


# ============================================================
# RAVITAILLEMENTS POTENTIELS
# ============================================================

def build_refueling_episodes(
    df_rules: pd.DataFrame,
) -> Dict:
    """
    Transforme les lignes de forte hausse
    en episodes de ravitaillement potentiels.

    Deux candidats du meme vehicule espaces
    de <= 10 minutes appartiennent
    au meme episode.
    """

    refuels = (
        df_rules[
            (
                df_rules[
                    "event_type"
                ]
                == "Ravitaillement potentiel"
            )
        ]
        .copy()
    )

    # --------------------------------------------------------
    # Aucun ravitaillement
    # --------------------------------------------------------

    if refuels.empty:

        empty_candidates = (
            refuels.copy()
        )

        empty_candidates[
            "gap_prev_candidate_sec"
        ] = pd.Series(
            index=
                empty_candidates.index,
            dtype="float64",
        )

        empty_candidates[
            "new_refuel_episode"
        ] = pd.Series(
            index=
                empty_candidates.index,
            dtype="bool",
        )

        empty_candidates[
            "episode_num"
        ] = pd.Series(
            index=
                empty_candidates.index,
            dtype="int64",
        )

        empty_candidates[
            "refuel_episode_id"
        ] = pd.Series(
            index=
                empty_candidates.index,
            dtype="object",
        )

        empty_episodes = (
            pd.DataFrame(
                columns=
                    REFUEL_EPISODE_COLUMNS
            )
        )

        return {
            "refuel_candidates":
                empty_candidates,

            "refueling_episodes":
                empty_episodes,
        }

    # --------------------------------------------------------
    # Tri
    # --------------------------------------------------------

    refuels = (
        refuels
        .sort_values(
            [
                "deviceId",
                "fixTime",
            ]
        )
        .copy()
    )

    # --------------------------------------------------------
    # Temps depuis le candidat precedent
    # --------------------------------------------------------

    refuels[
        "gap_prev_candidate_sec"
    ] = (
        refuels
        .groupby(
            "deviceId"
        )[
            "fixTime"
        ]
        .diff()
        .dt.total_seconds()
    )

    # --------------------------------------------------------
    # Debut d'un nouvel episode
    # --------------------------------------------------------

    refuels[
        "new_refuel_episode"
    ] = (
        refuels[
            "gap_prev_candidate_sec"
        ].isna()
        |
        (
            refuels[
                "gap_prev_candidate_sec"
            ]
            > MAX_GAP_REFUEL_SEC
        )
    )

    refuels[
        "episode_num"
    ] = (
        refuels
        .groupby(
            "deviceId"
        )[
            "new_refuel_episode"
        ]
        .cumsum()
        .astype(int)
    )

    refuels[
        "refuel_episode_id"
    ] = (
        "REF_"
        + refuels[
            "deviceId"
        ].astype(str)
        + "_"
        + refuels[
            "episode_num"
        ]
        .astype(str)
        .str.zfill(3)
    )

    # --------------------------------------------------------
    # Une ligne par episode
    # --------------------------------------------------------

    refueling_episodes = (
        refuels
        .groupby(
            [
                "deviceId",
                "refuel_episode_id",
            ],
            as_index=False,
        )
        .agg(
            start_time=(
                "fixTime",
                "min",
            ),

            end_time=(
                "fixTime",
                "max",
            ),

            n_steps=(
                "delta_fuel",
                "size",
            ),

            total_delta_fuel_pct=(
                "delta_fuel",
                "sum",
            ),

            start_fuel_pct=(
                "prev_fuel",
                "first",
            ),

            end_fuel_pct=(
                "fuelLevel",
                "last",
            ),

            max_speed_kmh=(
                "speed_kmh",
                "max",
            ),

            mean_speed_kmh=(
                "speed_kmh",
                "mean",
            ),
        )
    )

    refueling_episodes[
        "duration_sec"
    ] = (
        (
            refueling_episodes[
                "end_time"
            ]
            -
            refueling_episodes[
                "start_time"
            ]
        )
        .dt.total_seconds()
    )

    refueling_episodes = (
        refueling_episodes[
            REFUEL_EPISODE_COLUMNS
        ]
    )

    return {
        "refuel_candidates":
            refuels,

        "refueling_episodes":
            refueling_episodes,
    }


# ============================================================
# BAISSES SUSPECTES
# ============================================================

def build_suspicious_events(
    df_rules: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construit la table finale des baisses
    suspectes detectees par les regles.
    """

    suspicious = (
        df_rules[
            (
                df_rules[
                    "event_type"
                ]
                ==
                "Baisse suspecte / anomalie potentielle"
            )
        ]
        .copy()
    )

    # --------------------------------------------------------
    # Aucun evenement suspect
    # --------------------------------------------------------

    if suspicious.empty:

        return pd.DataFrame(
            columns=
                SUSPICIOUS_EVENT_COLUMNS
        )

    suspicious = (
        suspicious
        .sort_values(
            [
                "deviceId",
                "fixTime",
            ]
        )
        .copy()
    )

    # --------------------------------------------------------
    # Amplitude de la baisse
    # --------------------------------------------------------

    suspicious[
        "drop_abs_pct"
    ] = (
        suspicious[
            "delta_fuel"
        ]
        .abs()
    )

    # --------------------------------------------------------
    # Vitesse de baisse
    # --------------------------------------------------------

    suspicious[
        "drop_rate_pct_per_min"
    ] = np.where(
        (
            suspicious[
                "delta_time_min"
            ] > 0
        ),

        (
            suspicious[
                "drop_abs_pct"
            ]
            /
            suspicious[
                "delta_time_min"
            ]
        ),

        np.nan,
    )

    # --------------------------------------------------------
    # Distance
    # --------------------------------------------------------

    suspicious[
        "distance_abs_m"
    ] = (
        suspicious[
            "delta_odometer_m"
        ]
        .abs()
    )

    # --------------------------------------------------------
    # Temps depuis la baisse suspecte precedente
    # --------------------------------------------------------

    suspicious[
        "gap_prev_suspect_sec"
    ] = (
        suspicious
        .groupby(
            "deviceId"
        )[
            "fixTime"
        ]
        .diff()
        .dt.total_seconds()
    )

    # --------------------------------------------------------
    # Numero d'evenement
    # --------------------------------------------------------

    suspicious[
        "suspect_event_num"
    ] = (
        suspicious
        .groupby(
            "deviceId"
        )
        .cumcount()
        + 1
    )

    # --------------------------------------------------------
    # Identifiant
    # --------------------------------------------------------

    suspicious[
        "suspicious_event_id"
    ] = (
        "SUS_"
        + suspicious[
            "deviceId"
        ].astype(str)
        + "_"
        + suspicious[
            "suspect_event_num"
        ]
        .astype(str)
        .str.zfill(3)
    )

    suspicious_events = (
        suspicious[
            SUSPICIOUS_EVENT_COLUMNS
        ]
        .sort_values(
            "drop_abs_pct",
            ascending=False,
        )
    )

    return (
        suspicious_events
    )


# ============================================================
# IDENTIFIANTS D'EVENEMENTS DANS LE DATASET
# ============================================================

def attach_event_ids(
    df_rules: pd.DataFrame,
    refuel_candidates: pd.DataFrame,
    suspicious_events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Ajoute event_id au dataset ligne par ligne.
    """

    result = (
        df_rules.copy()
    )

    result[
        "event_id"
    ] = pd.NA

    # --------------------------------------------------------
    # Ravitaillements
    # --------------------------------------------------------

    if not refuel_candidates.empty:

        result.loc[
            refuel_candidates.index,
            "event_id",
        ] = (
            refuel_candidates[
                "refuel_episode_id"
            ]
        )

    # --------------------------------------------------------
    # Baisses suspectes
    # --------------------------------------------------------

    if not suspicious_events.empty:

        suspicious_ids = (
            suspicious_events[
                [
                    "deviceId",
                    "fixTime",
                    "suspicious_event_id",
                ]
            ]
        )

        id_map = {
            (
                row.deviceId,
                row.fixTime,
            ):
                row.suspicious_event_id

            for row in (
                suspicious_ids
                .itertuples(
                    index=False
                )
            )
        }

        mask = (
            result[
                "event_type"
            ]
            ==
            "Baisse suspecte / anomalie potentielle"
        )

        result.loc[
            mask,
            "event_id",
        ] = [
            id_map.get(
                (
                    device_id,
                    fix_time,
                )
            )

            for (
                device_id,
                fix_time,
            )
            in zip(
                result.loc[
                    mask,
                    "deviceId",
                ],
                result.loc[
                    mask,
                    "fixTime",
                ],
            )
        ]

    return result


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def detect_rule_events(
    df_prepared: pd.DataFrame,
) -> Dict:
    """
    Execute toute la detection par regles.

    Le pipeline reste exploitable meme lorsqu'il
    n'existe aucune hausse ou aucune baisse carburant.

    Retourne :
    - dataset classifie ;
    - seuils calcules ;
    - candidats de ravitaillement ;
    - episodes de ravitaillement ;
    - baisses suspectes ;
    - statistiques principales.
    """

    # --------------------------------------------------------
    # 1. Seuils statistiques
    # --------------------------------------------------------

    thresholds = (
        compute_rule_thresholds(
            df_prepared
        )
    )

    # --------------------------------------------------------
    # 2. Variables de contexte
    # --------------------------------------------------------

    context_result = (
        add_rule_context(
            df_prepared,
            thresholds[
                "seuil_ravitaillement"
            ],
        )
    )

    df_rules = (
        context_result[
            "df_rules"
        ]
    )

    thresholds[
        "seuil_vitesse_arret_kmh"
    ] = (
        context_result[
            "seuil_vitesse_arret_kmh"
        ]
    )

    thresholds[
        "seuil_distance_m"
    ] = (
        SEUIL_DISTANCE_M
    )

    thresholds[
        "seuil_temps_rapide_sec"
    ] = (
        SEUIL_TEMPS_RAPIDE_SEC
    )

    thresholds[
        "max_gap_refuel_sec"
    ] = (
        MAX_GAP_REFUEL_SEC
    )

    # --------------------------------------------------------
    # 3. Classification
    # --------------------------------------------------------

    df_rules = (
        classify_fuel_events(
            df_rules,

            thresholds[
                "seuil_ravitaillement"
            ],

            thresholds[
                "seuil_baisse_forte"
            ],
        )
    )

    # --------------------------------------------------------
    # 4. Ravitaillements
    # --------------------------------------------------------

    refuel_result = (
        build_refueling_episodes(
            df_rules
        )
    )

    refuel_candidates = (
        refuel_result[
            "refuel_candidates"
        ]
    )

    refueling_episodes = (
        refuel_result[
            "refueling_episodes"
        ]
    )

    # --------------------------------------------------------
    # 5. Baisses suspectes
    # --------------------------------------------------------

    suspicious_events = (
        build_suspicious_events(
            df_rules
        )
    )

    # --------------------------------------------------------
    # 6. Identifiants d'evenements
    # --------------------------------------------------------

    df_rules = (
        attach_event_ids(
            df_rules,
            refuel_candidates,
            suspicious_events,
        )
    )

    # --------------------------------------------------------
    # 7. Resume
    # --------------------------------------------------------

    summary = {
        "nombre_lignes_classifiees":
            int(
                len(
                    df_rules
                )
            ),

        "nombre_candidats_refuel":
            int(
                len(
                    refuel_candidates
                )
            ),

        "nombre_episodes_refuel":
            int(
                len(
                    refueling_episodes
                )
            ),

        "nombre_baisses_suspectes":
            int(
                len(
                    suspicious_events
                )
            ),

        "nombre_incoherences_transition":
            int(
                (
                    df_rules[
                        "event_type"
                    ]
                    == "Incohérence de mesure"
                )
                .sum()
            ),
    }

    return {
        "df_rules":
            df_rules,

        "thresholds":
            thresholds,

        "refuel_candidates":
            refuel_candidates,

        "refueling_episodes":
            refueling_episodes,

        "suspicious_events":
            suspicious_events,

        "summary":
            summary,
    }