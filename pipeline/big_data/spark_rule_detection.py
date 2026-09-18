from typing import Dict, Optional

import pandas as pd

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window


# ============================================================
# PARAMETRES
# ============================================================

Q_SEUIL = 0.995

SEUIL_DISTANCE_M = 100

SEUIL_TEMPS_RAPIDE_SEC = 30 * 60

MAX_GAP_REFUEL_SEC = 10 * 60


# ============================================================
# COLONNES EVENEMENTS
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
# OUTILS
# ============================================================

def dataframe_is_empty(
    df: DataFrame,
) -> bool:
    """
    Vérifie si un DataFrame Spark est vide.
    """

    return (
        df.limit(1).count()
        == 0
    )


def exact_percentile(
    df: DataFrame,
    column: str,
    quantile: float,
) -> Optional[float]:
    """
    Calcule un percentile Spark exact.

    On utilise percentile() et non approxQuantile()
    afin de rester le plus proche possible du calcul
    Pandas utilisé dans le pipeline de référence.
    """

    clean = (
        df
        .select(
            F.col(
                column
            ).cast("double").alias(
                column
            )
        )
        .filter(
            F.col(
                column
            ).isNotNull()
        )
    )

    if dataframe_is_empty(
        clean
    ):
        return None

    value = (
        clean
        .agg(
            F.expr(
                f"percentile({column}, {quantile})"
            ).alias(
                "percentile_value"
            )
        )
        .first()[
            "percentile_value"
        ]
    )

    if value is None:
        return None

    return float(
        value
    )


# ============================================================
# POPULATION DE REFERENCE
# ============================================================

def build_reference_population_spark(
    df: DataFrame,
) -> Dict:
    """
    Reproduit la population de référence
    utilisée par rule_detection.py.

    Les véhicules ayant au moins une valeur
    fuelLevel hors [0,100] sont exclus
    du calcul des seuils.
    """

    vehicles_quality_df = (
        df
        .filter(
            (
                F.col(
                    "fuelLevel"
                ) < F.lit(0)
            )
            |
            (
                F.col(
                    "fuelLevel"
                ) > F.lit(100)
            )
        )
        .select(
            "deviceId"
        )
        .filter(
            F.col(
                "deviceId"
            ).isNotNull()
        )
        .distinct()
    )

    vehicles_excluded = [
        row[
            "deviceId"
        ]
        for row in (
            vehicles_quality_df.collect()
        )
    ]

    # --------------------------------------------------------
    # Population principale
    # --------------------------------------------------------

    if vehicles_excluded:

        reference = (
            df
            .filter(
                ~F.col(
                    "deviceId"
                ).isin(
                    vehicles_excluded
                )
            )
            .filter(
                F.col(
                    "delta_fuel"
                ).isNotNull()
            )
            .filter(
                ~F.coalesce(
                    F.col(
                        "flag_incoherence_fuel"
                    ),
                    F.lit(False),
                )
            )
        )

    else:

        reference = (
            df
            .filter(
                F.col(
                    "delta_fuel"
                ).isNotNull()
            )
            .filter(
                ~F.coalesce(
                    F.col(
                        "flag_incoherence_fuel"
                    ),
                    F.lit(False),
                )
            )
        )

    # --------------------------------------------------------
    # Sécurité :
    # si la population est vide, même fallback que Pandas.
    # --------------------------------------------------------

    if dataframe_is_empty(
        reference
    ):

        reference = (
            df
            .filter(
                F.col(
                    "delta_fuel"
                ).isNotNull()
            )
            .filter(
                ~F.coalesce(
                    F.col(
                        "flag_incoherence_fuel"
                    ),
                    F.lit(False),
                )
            )
        )

    return {
        "reference":
            reference,

        "vehicles_excluded_from_thresholds":
            vehicles_excluded,
    }


# ============================================================
# CALCUL DES SEUILS
# ============================================================

def compute_rule_thresholds_spark(
    df: DataFrame,
) -> Dict:
    """
    Calcule les seuils de hausse et de baisse
    avec le quantile 99,5 %.

    Aucun seuil artificiel n'est créé si
    aucune hausse ou baisse n'existe.
    """

    reference_result = (
        build_reference_population_spark(
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

    positives = (
        reference
        .filter(
            F.col(
                "delta_fuel"
            ) > F.lit(0)
        )
        .select(
            F.col(
                "delta_fuel"
            ).cast(
                "double"
            ).alias(
                "variation"
            )
        )
    )

    positive_count = (
        positives.count()
    )

    if positive_count == 0:

        seuil_ravitaillement = None

    else:

        seuil_ravitaillement = (
            exact_percentile(
                positives,
                "variation",
                Q_SEUIL,
            )
        )

    # --------------------------------------------------------
    # Variations négatives en valeur absolue
    # --------------------------------------------------------

    negatives = (
        reference
        .filter(
            F.col(
                "delta_fuel"
            ) < F.lit(0)
        )
        .select(
            F.abs(
                F.col(
                    "delta_fuel"
                ).cast(
                    "double"
                )
            ).alias(
                "variation"
            )
        )
    )

    negative_count = (
        negatives.count()
    )

    if negative_count == 0:

        seuil_baisse_forte = None

    else:

        seuil_baisse_forte = (
            exact_percentile(
                negatives,
                "variation",
                Q_SEUIL,
            )
        )

    reference_count = (
        reference.count()
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
                positive_count
            ),

        "nombre_variations_negatives_reference":
            int(
                negative_count
            ),

        "vehicles_excluded_from_thresholds":
            reference_result[
                "vehicles_excluded_from_thresholds"
            ],

        "nombre_lignes_reference":
            int(
                reference_count
            ),
    }


# ============================================================
# CONTEXTE DES REGLES
# ============================================================

def add_rule_context_spark(
    df: DataFrame,
    seuil_ravitaillement: Optional[
        float
    ],
) -> Dict:
    """
    Ajoute les variables de contexte utilisées
    par les règles métier.
    """

    df_rules = df

    # --------------------------------------------------------
    # Candidats de forte hausse
    # --------------------------------------------------------

    if seuil_ravitaillement is None:

        candidats_hausse = (
            df_rules.limit(0)
        )

    else:

        candidats_hausse = (
            df_rules
            .filter(
                ~F.coalesce(
                    F.col(
                        "flag_incoherence_fuel"
                    ),
                    F.lit(False),
                )
            )
            .filter(
                F.col(
                    "delta_fuel"
                )
                > F.lit(
                    seuil_ravitaillement
                )
            )
        )

    # --------------------------------------------------------
    # Seuil vitesse arrêt
    # --------------------------------------------------------

    if dataframe_is_empty(
        candidats_hausse
    ):

        seuil_vitesse_arret_kmh = (
            10.0
        )

    else:

        speed_candidates = (
            candidats_hausse
            .select(
                F.col(
                    "speed_kmh"
                ).cast(
                    "double"
                ).alias(
                    "speed_value"
                )
            )
            .filter(
                F.col(
                    "speed_value"
                ).isNotNull()
            )
        )

        speed_quantile = (
            exact_percentile(
                speed_candidates,
                "speed_value",
                0.95,
            )
        )

        if speed_quantile is None:

            seuil_vitesse_arret_kmh = (
                10.0
            )

        else:

            seuil_vitesse_arret_kmh = (
                float(
                    speed_quantile
                )
            )

    # --------------------------------------------------------
    # Mouvement significatif
    # --------------------------------------------------------

    speed_movement = (
        F.coalesce(
            (
                F.col(
                    "speed_kmh"
                )
                >
                F.lit(
                    seuil_vitesse_arret_kmh
                )
            ),
            F.lit(False),
        )
    )

    odometer_movement = (
        F.coalesce(
            (
                F.abs(
                    F.col(
                        "delta_odometer_m"
                    )
                )
                >
                F.lit(
                    SEUIL_DISTANCE_M
                )
            ),
            F.lit(False),
        )
    )

    df_rules = (
        df_rules
        .withColumn(
            "mouvement_significatif",
            (
                speed_movement
                |
                odometer_movement
            ),
        )
    )

    # --------------------------------------------------------
    # Arrêt probable
    # --------------------------------------------------------

    speed_stopped = (
        F.coalesce(
            (
                F.col(
                    "speed_kmh"
                )
                <=
                F.lit(
                    seuil_vitesse_arret_kmh
                )
            ),
            F.lit(False),
        )
    )

    distance_stopped = (
        F.coalesce(
            (
                F.abs(
                    F.col(
                        "delta_odometer_m"
                    )
                )
                <=
                F.lit(
                    SEUIL_DISTANCE_M
                )
            ),
            F.lit(False),
        )
    )

    df_rules = (
        df_rules
        .withColumn(
            "arret_probable",
            (
                speed_stopped
                &
                distance_stopped
            ),
        )
    )

    # --------------------------------------------------------
    # Ignition OFF
    # --------------------------------------------------------

    df_rules = (
        df_rules
        .withColumn(
            "ignition_off_support",
            F.coalesce(
                (
                    F.col(
                        "ignition"
                    )
                    ==
                    F.lit(False)
                ),
                F.lit(False),
            ),
        )
    )

    # --------------------------------------------------------
    # Variation rapide
    # --------------------------------------------------------

    df_rules = (
        df_rules
        .withColumn(
            "variation_rapide",
            F.coalesce(
                (
                    F.col(
                        "delta_time_sec"
                    )
                    <=
                    F.lit(
                        SEUIL_TEMPS_RAPIDE_SEC
                    )
                ),
                F.lit(False),
            ),
        )
    )

    return {
        "df_rules":
            df_rules,

        "seuil_vitesse_arret_kmh":
            seuil_vitesse_arret_kmh,
    }


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_fuel_events_spark(
    df: DataFrame,
    seuil_ravitaillement: Optional[
        float
    ],
    seuil_baisse_forte: Optional[
        float
    ],
) -> DataFrame:
    """
    Même priorité que le pipeline Pandas :

    1. incohérence
    2. ravitaillement
    3. baisse suspecte
    4. consommation normale
    """

    condition_incoherence = (
        F.coalesce(
            F.col(
                "flag_incoherence_fuel"
            ),
            F.lit(False),
        )
    )

    # --------------------------------------------------------
    # Ravitaillement
    # --------------------------------------------------------

    if seuil_ravitaillement is None:

        condition_ravitaillement = (
            F.lit(False)
        )

    else:

        condition_ravitaillement = (
            (~condition_incoherence)
            &
            (
                F.col(
                    "delta_fuel"
                )
                >
                F.lit(
                    seuil_ravitaillement
                )
            )
        )

    # --------------------------------------------------------
    # Baisse suspecte
    # --------------------------------------------------------

    if seuil_baisse_forte is None:

        condition_baisse_suspecte = (
            F.lit(False)
        )

    else:

        condition_baisse_suspecte = (
            (~condition_incoherence)
            &
            (~condition_ravitaillement)
            &
            (
                F.col(
                    "delta_fuel"
                )
                <
                F.lit(
                    -seuil_baisse_forte
                )
            )
            &
            F.col(
                "variation_rapide"
            )
            &
            F.col(
                "arret_probable"
            )
        )

    # --------------------------------------------------------
    # Type d'événement
    # --------------------------------------------------------

    df_rules = (
        df
        .withColumn(
            "event_type",
            F.when(
                F.col(
                    "delta_fuel"
                ).isNull(),
                F.lit(None).cast(
                    "string"
                ),
            )
            .when(
                condition_incoherence,
                F.lit(
                    "Incohérence de mesure"
                ),
            )
            .when(
                condition_ravitaillement,
                F.lit(
                    "Ravitaillement potentiel"
                ),
            )
            .when(
                condition_baisse_suspecte,
                F.lit(
                    "Baisse suspecte / anomalie potentielle"
                ),
            )
            .otherwise(
                F.lit(
                    "Consommation normale"
                )
            ),
        )
    )

    # --------------------------------------------------------
    # Raison
    # --------------------------------------------------------

    reason = (
        F.when(
            F.col(
                "delta_fuel"
            ).isNull(),
            F.lit(None).cast(
                "string"
            ),
        )
        .when(
            condition_incoherence,
            F.lit(
                "Valeur actuelle ou précédente de "
                "fuelLevel hors de la plage 0-100 %"
            ),
        )
        .when(
            (
                condition_ravitaillement
                &
                F.col(
                    "arret_probable"
                )
            ),
            F.lit(
                "Hausse extrême de fuelLevel + "
                "véhicule proche de l'arrêt"
            ),
        )
        .when(
            condition_ravitaillement,
            F.lit(
                "Hausse extrême de fuelLevel ; "
                "contexte mouvement à vérifier"
            ),
        )
        .when(
            (
                condition_baisse_suspecte
                &
                F.col(
                    "ignition_off_support"
                )
            ),
            F.lit(
                "Baisse extrême et rapide + "
                "véhicule immobile + "
                "ignition=False en support"
            ),
        )
        .when(
            condition_baisse_suspecte,
            F.lit(
                "Baisse extrême et rapide + "
                "véhicule immobile selon "
                "vitesse/odomètre"
            ),
        )
        .otherwise(
            F.lit(
                "Variation non signalée par "
                "les règles de niveau 1"
            )
        )
    )

    return (
        df_rules
        .withColumn(
            "event_reason",
            reason,
        )
    )


# ============================================================
# RAVITAILLEMENTS
# ============================================================

def build_refueling_episodes_spark(
    df_rules: DataFrame,
) -> Dict:
    """
    Regroupe les fortes hausses espacées
    de 10 minutes ou moins.
    """

    refuels = (
        df_rules
        .filter(
            F.col(
                "event_type"
            )
            ==
            F.lit(
                "Ravitaillement potentiel"
            )
        )
    )

    if dataframe_is_empty(
        refuels
    ):

        empty_candidates = (
            pd.DataFrame()
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

            "refuel_candidates_spark":
                refuels,
        }

    # --------------------------------------------------------
    # Fenêtre chronologique
    # --------------------------------------------------------

    window_vehicle = (
        Window
        .partitionBy(
            "deviceId"
        )
        .orderBy(
            "fixTime"
        )
    )

    refuels = (
        refuels
        .withColumn(
            "previous_refuel_time",
            F.lag(
                "fixTime"
            ).over(
                window_vehicle
            ),
        )
        .withColumn(
            "gap_prev_candidate_sec",
            (
                F.col(
                    "fixTime"
                ).cast(
                    "long"
                )
                -
                F.col(
                    "previous_refuel_time"
                ).cast(
                    "long"
                )
            ).cast(
                "double"
            ),
        )
    )

    refuels = (
        refuels
        .withColumn(
            "new_refuel_episode",
            (
                F.col(
                    "previous_refuel_time"
                ).isNull()
                |
                (
                    F.col(
                        "gap_prev_candidate_sec"
                    )
                    >
                    F.lit(
                        MAX_GAP_REFUEL_SEC
                    )
                )
            ),
        )
    )

    cumulative_window = (
        window_vehicle
        .rowsBetween(
            Window.unboundedPreceding,
            Window.currentRow,
        )
    )

    refuels = (
        refuels
        .withColumn(
            "episode_num",
            F.sum(
                F.when(
                    F.col(
                        "new_refuel_episode"
                    ),
                    F.lit(1),
                ).otherwise(
                    F.lit(0)
                )
            ).over(
                cumulative_window
            ),
        )
        .withColumn(
            "refuel_episode_id",
            F.concat(
                F.lit(
                    "REF_"
                ),
                F.col(
                    "deviceId"
                ).cast(
                    "string"
                ),
                F.lit(
                    "_"
                ),
                F.lpad(
                    F.col(
                        "episode_num"
                    ).cast(
                        "string"
                    ),
                    3,
                    "0",
                ),
            ),
        )
    )

    # --------------------------------------------------------
    # Une ligne par épisode
    # --------------------------------------------------------

    episodes = (
        refuels
        .groupBy(
            "deviceId",
            "refuel_episode_id",
        )
        .agg(
            F.min(
                "fixTime"
            ).alias(
                "start_time"
            ),

            F.max(
                "fixTime"
            ).alias(
                "end_time"
            ),

            F.count(
                F.lit(1)
            ).alias(
                "n_steps"
            ),

            F.sum(
                "delta_fuel"
            ).alias(
                "total_delta_fuel_pct"
            ),

            F.min_by(
                F.col(
                    "prev_fuel"
                ),
                F.col(
                    "fixTime"
                ),
            ).alias(
                "start_fuel_pct"
            ),

            F.max_by(
                F.col(
                    "fuelLevel"
                ),
                F.col(
                    "fixTime"
                ),
            ).alias(
                "end_fuel_pct"
            ),

            F.max(
                "speed_kmh"
            ).alias(
                "max_speed_kmh"
            ),

            F.avg(
                "speed_kmh"
            ).alias(
                "mean_speed_kmh"
            ),
        )
        .withColumn(
            "duration_sec",
            (
                F.col(
                    "end_time"
                ).cast(
                    "long"
                )
                -
                F.col(
                    "start_time"
                ).cast(
                    "long"
                )
            ).cast(
                "double"
            ),
        )
        .select(
            *REFUEL_EPISODE_COLUMNS
        )
    )

    # --------------------------------------------------------
    # Conversion uniquement des petites tables
    # --------------------------------------------------------

    refuel_candidates = (
        refuels
        .drop(
            "previous_refuel_time"
        )
        .orderBy(
            "deviceId",
            "fixTime",
        )
        .toPandas()
    )

    refueling_episodes = (
        episodes
        .orderBy(
            "deviceId",
            "start_time",
        )
        .toPandas()
    )

    return {
        "refuel_candidates":
            refuel_candidates,

        "refueling_episodes":
            refueling_episodes,

        "refuel_candidates_spark":
            refuels,
    }


# ============================================================
# BAISSES SUSPECTES
# ============================================================

def build_suspicious_events_spark(
    df_rules: DataFrame,
) -> Dict:
    """
    Construit les baisses suspectes avec Spark,
    puis convertit uniquement cette petite table.
    """

    suspicious = (
        df_rules
        .filter(
            F.col(
                "event_type"
            )
            ==
            F.lit(
                "Baisse suspecte / anomalie potentielle"
            )
        )
    )

    if dataframe_is_empty(
        suspicious
    ):

        return {
            "suspicious_events":
                pd.DataFrame(
                    columns=
                        SUSPICIOUS_EVENT_COLUMNS
                ),

            "suspicious_events_spark":
                suspicious,
        }

    suspicious = (
        suspicious
        .withColumn(
            "drop_abs_pct",
            F.abs(
                F.col(
                    "delta_fuel"
                )
            ),
        )
        .withColumn(
            "drop_rate_pct_per_min",
            F.when(
                F.col(
                    "delta_time_min"
                ) > F.lit(0),
                (
                    F.abs(
                        F.col(
                            "delta_fuel"
                        )
                    )
                    /
                    F.col(
                        "delta_time_min"
                    )
                ),
            ).otherwise(
                F.lit(None).cast(
                    "double"
                )
            ),
        )
        .withColumn(
            "distance_abs_m",
            F.abs(
                F.col(
                    "delta_odometer_m"
                )
            ),
        )
    )

    suspicious_window = (
        Window
        .partitionBy(
            "deviceId"
        )
        .orderBy(
            "fixTime"
        )
    )

    suspicious = (
        suspicious
        .withColumn(
            "previous_suspicious_time",
            F.lag(
                "fixTime"
            ).over(
                suspicious_window
            ),
        )
        .withColumn(
            "gap_prev_suspect_sec",
            (
                F.col(
                    "fixTime"
                ).cast(
                    "long"
                )
                -
                F.col(
                    "previous_suspicious_time"
                ).cast(
                    "long"
                )
            ).cast(
                "double"
            ),
        )
        .withColumn(
            "suspect_event_num",
            F.row_number().over(
                suspicious_window
            ),
        )
        .withColumn(
            "suspicious_event_id",
            F.concat(
                F.lit(
                    "SUS_"
                ),
                F.col(
                    "deviceId"
                ).cast(
                    "string"
                ),
                F.lit(
                    "_"
                ),
                F.lpad(
                    F.col(
                        "suspect_event_num"
                    ).cast(
                        "string"
                    ),
                    3,
                    "0",
                ),
            ),
        )
    )

    suspicious_events_spark = (
        suspicious
        .select(
            *SUSPICIOUS_EVENT_COLUMNS
        )
    )

    suspicious_events = (
        suspicious_events_spark
        .orderBy(
            F.col(
                "drop_abs_pct"
            ).desc()
        )
        .toPandas()
    )

    return {
        "suspicious_events":
            suspicious_events,

        "suspicious_events_spark":
            suspicious_events_spark,
    }


# ============================================================
# EVENT IDs DANS LE DATASET SPARK
# ============================================================

def attach_event_ids_spark(
    df_rules: DataFrame,
    refuel_candidates_spark: DataFrame,
    suspicious_events_spark: DataFrame,
) -> DataFrame:
    """
    Ajoute event_id au dataset Spark.

    Les petites tables d'événements sont utilisées
    comme tables de correspondance.
    """

    result = (
        df_rules
        .withColumn(
            "event_id",
            F.lit(None).cast(
                "string"
            ),
        )
    )

    # --------------------------------------------------------
    # Ravitaillements
    # --------------------------------------------------------

    if not dataframe_is_empty(
        refuel_candidates_spark
    ):

        refuel_map = (
            refuel_candidates_spark
            .select(
                "deviceId",
                "fixTime",
                "refuel_episode_id",
            )
            .dropDuplicates(
                [
                    "deviceId",
                    "fixTime",
                ]
            )
        )

        result = (
            result
            .join(
                F.broadcast(
                    refuel_map
                ),
                on=[
                    "deviceId",
                    "fixTime",
                ],
                how="left",
            )
            .withColumn(
                "event_id",
                F.coalesce(
                    F.col(
                        "refuel_episode_id"
                    ),
                    F.col(
                        "event_id"
                    ),
                ),
            )
            .drop(
                "refuel_episode_id"
            )
        )

    # --------------------------------------------------------
    # Baisses suspectes
    # --------------------------------------------------------

    if not dataframe_is_empty(
        suspicious_events_spark
    ):

        suspicious_map = (
            suspicious_events_spark
            .select(
                "deviceId",
                "fixTime",
                "suspicious_event_id",
            )
            .dropDuplicates(
                [
                    "deviceId",
                    "fixTime",
                ]
            )
        )

        result = (
            result
            .join(
                F.broadcast(
                    suspicious_map
                ),
                on=[
                    "deviceId",
                    "fixTime",
                ],
                how="left",
            )
            .withColumn(
                "event_id",
                F.coalesce(
                    F.col(
                        "suspicious_event_id"
                    ),
                    F.col(
                        "event_id"
                    ),
                ),
            )
            .drop(
                "suspicious_event_id"
            )
        )

    return result


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def detect_rule_events_spark(
    df_prepared: DataFrame,
) -> Dict:
    """
    Version Spark de detect_rule_events().

    Les millions de lignes restent dans Spark.

    Seules les petites tables d'événements sont
    converties en Pandas.
    """

    # --------------------------------------------------------
    # 1. Seuils
    # --------------------------------------------------------

    thresholds = (
        compute_rule_thresholds_spark(
            df_prepared
        )
    )

    # --------------------------------------------------------
    # 2. Variables de contexte
    # --------------------------------------------------------

    context_result = (
        add_rule_context_spark(
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
        classify_fuel_events_spark(
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
        build_refueling_episodes_spark(
            df_rules
        )
    )

    refueling_episodes = (
        refuel_result[
            "refueling_episodes"
        ]
    )

    # --------------------------------------------------------
    # 5. Baisses suspectes
    # --------------------------------------------------------

    suspicious_result = (
        build_suspicious_events_spark(
            df_rules
        )
    )

    suspicious_events = (
        suspicious_result[
            "suspicious_events"
        ]
    )

    # --------------------------------------------------------
    # 6. IDs
    # --------------------------------------------------------

    df_rules = (
        attach_event_ids_spark(
            df_rules,

            refuel_result[
                "refuel_candidates_spark"
            ],

            suspicious_result[
                "suspicious_events_spark"
            ],
        )
    )

    # --------------------------------------------------------
    # 7. Résumé
    # --------------------------------------------------------

    nombre_lignes_classifiees = (
        df_rules.count()
    )

    nombre_incoherences = (
        df_rules
        .filter(
            F.col(
                "event_type"
            )
            ==
            F.lit(
                "Incohérence de mesure"
            )
        )
        .count()
    )

    summary = {
        "nombre_lignes_classifiees":
            int(
                nombre_lignes_classifiees
            ),

        "nombre_candidats_refuel":
            int(
                len(
                    refuel_result[
                        "refuel_candidates"
                    ]
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
                nombre_incoherences
            ),
    }

    return {
        "df_rules":
            df_rules,

        "thresholds":
            thresholds,

        "refuel_candidates":
            refuel_result[
                "refuel_candidates"
            ],

        "refueling_episodes":
            refueling_episodes,

        "suspicious_events":
            suspicious_events,

        "summary":
            summary,
    }