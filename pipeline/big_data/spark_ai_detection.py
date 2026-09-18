from typing import Dict

import pandas as pd

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


from anomaly_detection.isolation_forest import (
    train_isolation_forest_models,
    build_ai_top_candidates,
    build_ai_vehicle_summary,
    compare_rules_and_ai,
)


# ============================================================
# PREPARATION SPARK DES BAISSES POUR L'IA
# ============================================================

def prepare_ai_candidates_spark(
    df_rules: DataFrame,
) -> DataFrame:
    """
    Sélectionne avec Spark uniquement les baisses
    exploitables par Isolation Forest.

    Cette fonction reproduit la logique de
    prepare_ai_candidates() sans convertir tout
    le dataset Spark en Pandas.
    """

    required_columns = [
        "deviceId",
        "fixTime",
        "fuelLevel",
        "delta_fuel",
        "delta_time_sec",
        "speed_kmh",
        "delta_odometer_m",
        "ignition",
        "flag_incoherence_fuel",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df_rules.columns
    ]

    if missing_columns:

        raise ValueError(
            "Impossible d'executer Isolation Forest. "
            f"Colonnes manquantes : {missing_columns}"
        )

    df_ai = df_rules

    # ========================================================
    # CONVERSION NUMERIQUE
    # ========================================================

    numeric_columns = [
        "fuelLevel",
        "delta_fuel",
        "delta_time_sec",
        "speed_kmh",
        "delta_odometer_m",
    ]

    for column in numeric_columns:

        df_ai = (
            df_ai
            .withColumn(
                column,
                F.col(
                    column
                ).cast(
                    "double"
                ),
            )
        )

    # ========================================================
    # IGNITION -> 0 / 1
    # ========================================================

    ignition_text = (
        F.lower(
            F.trim(
                F.col(
                    "ignition"
                ).cast(
                    "string"
                )
            )
        )
    )

    ignition_ai = (
        F.when(
            ignition_text.isin(
                "true",
                "1",
            ),
            F.lit(
                1.0
            ),
        )
        .when(
            ignition_text.isin(
                "false",
                "0",
            ),
            F.lit(
                0.0
            ),
        )
        .otherwise(
            F.coalesce(
                F.col(
                    "ignition"
                ).cast(
                    "double"
                ),
                F.lit(
                    0.0
                ),
            )
        )
    )

    df_ai = (
        df_ai
        .withColumn(
            "ignition_ai",
            ignition_ai,
        )
    )

    # ========================================================
    # IDENTIFIANT DE L'ALERTE REGLE
    # ========================================================

    if (
        "event_id"
        in df_ai.columns
    ):

        df_ai = (
            df_ai
            .withColumn(
                "suspicious_event_id",
                F.when(
                    F.col(
                        "event_id"
                    ).startswith(
                        "SUS_"
                    ),
                    F.col(
                        "event_id"
                    ),
                )
                .otherwise(
                    F.lit(
                        None
                    ).cast(
                        "string"
                    )
                ),
            )
        )

    else:

        df_ai = (
            df_ai
            .withColumn(
                "suspicious_event_id",
                F.lit(
                    None
                ).cast(
                    "string"
                ),
            )
        )

    # ========================================================
    # FLAG D'INCOHERENCE
    # ========================================================

    flag_incoherence = (
        F.coalesce(
            F.col(
                "flag_incoherence_fuel"
            ),
            F.lit(
                False
            ),
        )
    )

    # ========================================================
    # FILTRAGE DES BAISSES VALIDES
    # ========================================================

    df_ai = (
        df_ai
        .filter(
            F.col(
                "fuelLevel"
            ).between(
                0,
                100,
            )
        )
        .filter(
            ~flag_incoherence
        )
        .filter(
            F.col(
                "delta_fuel"
            )
            <
            F.lit(
                0
            )
        )
        .filter(
            F.col(
                "delta_time_sec"
            ).isNotNull()
        )
        .filter(
            F.col(
                "speed_kmh"
            ).isNotNull()
        )
        .filter(
            F.col(
                "delta_odometer_m"
            ).isNotNull()
        )
    )

    # ========================================================
    # FEATURE 1 : AMPLITUDE DE LA BAISSE
    # ========================================================

    df_ai = (
        df_ai
        .withColumn(
            "drop_abs_pct",
            -F.col(
                "delta_fuel"
            ),
        )
    )

    # ========================================================
    # FEATURE 2 : TEMPS LOGARITHMIQUE
    #
    # Pandas :
    # clip(lower=0, upper=24*3600)
    # puis np.log1p()
    # ========================================================

    clipped_time = (
        F.greatest(
            F.lit(
                0.0
            ),
            F.least(
                F.col(
                    "delta_time_sec"
                ),
                F.lit(
                    24 * 3600.0
                ),
            ),
        )
    )

    df_ai = (
        df_ai
        .withColumn(
            "log_delta_time",
            F.log1p(
                clipped_time
            ),
        )
    )

    # ========================================================
    # FEATURE 3 : DISTANCE ABSOLUE
    # ========================================================

    df_ai = (
        df_ai
        .withColumn(
            "distance_abs_m",
            F.abs(
                F.col(
                    "delta_odometer_m"
                )
            ),
        )
    )

    # ========================================================
    # FEATURE 4 : DISTANCE LOGARITHMIQUE
    #
    # Pandas :
    # clip(upper=100000)
    # puis np.log1p()
    # ========================================================

    clipped_distance = (
        F.least(
            F.col(
                "distance_abs_m"
            ),
            F.lit(
                100000.0
            ),
        )
    )

    df_ai = (
        df_ai
        .withColumn(
            "log_distance_abs",
            F.log1p(
                clipped_distance
            ),
        )
    )

    return df_ai


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def detect_ai_anomalies_spark(
    df_rules: DataFrame,
    suspicious_events: pd.DataFrame,
) -> Dict:
    """
    Version hybride Spark + Scikit-learn.

    Spark :
        filtre le gros volume et calcule les features.

    Pandas / Scikit-learn :
        entraînent Isolation Forest uniquement
        sur les baisses exploitables.
    """

    # ========================================================
    # 1. FILTRAGE SPARK
    # ========================================================

    ai_candidates_spark = (
        prepare_ai_candidates_spark(
            df_rules
        )
    )

    # ========================================================
    # 2. CONVERSION DU SOUS-ENSEMBLE UNIQUEMENT
    # ========================================================

    ai_candidates = (
        ai_candidates_spark
        .orderBy(
            "deviceId",
            "fixTime",
        )
        .toPandas()
    )

    # ========================================================
    # 3. ENTRAINEMENT ISOLATION FOREST EXISTANT
    # ========================================================

    training_results = (
        train_isolation_forest_models(
            ai_candidates
        )
    )

    ai_scores = (
        training_results[
            "ai_scores"
        ]
    )

    # ========================================================
    # 4. TOP 1 % IA
    # ========================================================

    ai_top = (
        build_ai_top_candidates(
            ai_scores
        )
    )

    # ========================================================
    # 5. RESUME PAR VEHICULE
    # ========================================================

    vehicle_summary = (
        build_ai_vehicle_summary(
            ai_scores
        )
    )

    # ========================================================
    # 6. COMPARAISON REGLES / IA
    # ========================================================

    comparison = (
        compare_rules_and_ai(
            ai_scores,
            suspicious_events,
        )
    )

    # ========================================================
    # 7. CANDIDATS IA UNIQUEMENT
    # ========================================================

    ai_only_candidates = (
        ai_top[
            ai_top[
                "suspicious_event_id"
            ].isna()
        ]
        .copy()
        .sort_values(
            "ai_score_percentile",
            ascending=False,
        )
    )

    # ========================================================
    # 8. RESUME GLOBAL
    # ========================================================

    global_summary = {
        "nombre_baisses_analysees":
            int(
                len(
                    ai_scores
                )
            ),

        "nombre_candidats_ia":
            int(
                ai_scores[
                    "ai_anomaly_flag"
                ]
                .fillna(
                    False
                )
                .astype(
                    bool
                )
                .sum()
            ),

        "nombre_alertes_regles":
            comparison[
                "nb_alertes_regles"
            ],

        "nombre_overlap_regles_ia":
            comparison[
                "nb_overlap_regles_ia"
            ],

        "taux_recouvrement_pct":
            comparison[
                "taux_recouvrement_pct"
            ],

        "nombre_candidats_ia_uniquement":
            int(
                len(
                    ai_only_candidates
                )
            ),

        "nombre_modeles_entraines":
            int(
                len(
                    training_results[
                        "models"
                    ]
                )
            ),
    }

    return {
        "ai_candidates":
            ai_candidates,

        "ai_scores":
            ai_scores,

        "ai_top_candidates":
            ai_top,

        "ai_model_summary":
            training_results[
                "ai_model_summary"
            ],

        "ai_vehicle_summary":
            vehicle_summary,

        "rules_vs_ai_comparison":
            comparison[
                "rules_vs_ai_comparison"
            ],

        "ai_only_candidates":
            ai_only_candidates,

        "summary":
            global_summary,

        "models":
            training_results[
                "models"
            ],

        "scalers":
            training_results[
                "scalers"
            ],

        "ignored_vehicles":
            training_results[
                "ignored_vehicles"
            ],

        # Utile uniquement pour vérifier que
        # le filtrage a réellement été fait par Spark.
        "ai_candidates_spark":
            ai_candidates_spark,
    }