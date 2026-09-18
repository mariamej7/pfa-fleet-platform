from typing import Dict, Optional

import pandas as pd

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


# ============================================================
# SEUILS KPI
# ============================================================

# Même logique que compute_kpis.py
SEUIL_MOUVEMENT_KPI_KMH = 5

# Un jour est actif si au moins 1 km est parcouru.
SEUIL_JOUR_ACTIF_KM = 1


# ============================================================
# COLONNES FINALES KPI VEHICULE
# ============================================================

KPI_VEHICLE_COLUMNS = [
    "deviceId",
    "nombre_mesures",
    "debut_periode",
    "fin_periode",

    "jours_calendaires_periode",
    "jours_avec_donnees",
    "jours_actifs",
    "taux_couverture_jours_pct",

    "distance_km",
    "distance_moyenne_par_jour_actif_km",

    "vitesse_moyenne_mesures_kmh",
    "vitesse_moyenne_en_mouvement_kmh",
    "vitesse_max_kmh",

    "fuel_moyen_pct",
    "fuel_min_pct",
    "fuel_max_pct",

    "nb_ravitaillements_potentiels",
    "hausse_moyenne_refuel_pct",
    "hausse_max_refuel_pct",

    "nb_baisses_suspectes",
    "baisse_moyenne_suspecte_pct",
    "baisse_max_suspecte_pct",

    "nb_incoherences_fuel",
    "pct_incoherences_fuel",
]


# ============================================================
# PREPARATION KPI SPARK
# ============================================================

def prepare_kpi_data_spark(
    df_prepared: DataFrame,
) -> DataFrame:
    """
    Prépare les variables nécessaires aux KPI
    directement dans Spark.

    Reproduit la logique de
    analytics/compute_kpis.py.
    """

    required_columns = [
        "deviceId",
        "fixTime",
        "speed_kmh",
        "fuelLevel",
        "odometer",
        "delta_odometer_m",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df_prepared.columns
    ]

    if missing_columns:
        raise ValueError(
            "Impossible de calculer les KPI Spark. "
            f"Colonnes manquantes : {missing_columns}"
        )

    df = df_prepared

    # --------------------------------------------------------
    # fuelLevel valide
    #
    # Les valeurs hors 0-100 restent présentes,
    # mais sont exclues des statistiques carburant.
    # --------------------------------------------------------

    df = df.withColumn(
        "fuelLevel_valide",
        F.when(
            F.col("fuelLevel").between(
                0,
                100,
            ),
            F.col("fuelLevel").cast("double"),
        ).otherwise(
            F.lit(None).cast("double")
        ),
    )

    # --------------------------------------------------------
    # Distance positive
    #
    # Même logique que :
    # delta_odometer_m.clip(lower=0)
    # --------------------------------------------------------

    df = df.withColumn(
        "distance_positive_m",
        F.when(
            F.col(
                "delta_odometer_m"
            ).isNull(),
            F.lit(None).cast("double"),
        ).otherwise(
            F.greatest(
                F.col(
                    "delta_odometer_m"
                ).cast("double"),
                F.lit(0.0),
            )
        ),
    )

    # --------------------------------------------------------
    # Véhicule en mouvement
    # --------------------------------------------------------

    df = df.withColumn(
        "en_mouvement_kpi",
        (
            F.col("speed_kmh")
            > F.lit(
                SEUIL_MOUVEMENT_KPI_KMH
            )
        ),
    )

    # --------------------------------------------------------
    # Date sans heure
    # --------------------------------------------------------

    df = df.withColumn(
        "date",
        F.to_date(
            F.col("fixTime")
        ),
    )

    return df


# ============================================================
# KPI JOURNALIERS SPARK
# ============================================================

def compute_daily_kpis_spark(
    df_kpi: DataFrame,
) -> DataFrame:
    """
    Une ligne par véhicule et par jour.
    """

    kpi_daily = (
        df_kpi
        .filter(
            F.col("date").isNotNull()
        )
        .groupBy(
            "deviceId",
            "date",
        )
        .agg(
            F.count(
                F.lit(1)
            ).alias(
                "nombre_mesures"
            ),

            (
                F.sum(
                    "distance_positive_m"
                )
                / F.lit(1000.0)
            ).alias(
                "distance_km"
            ),

            F.avg(
                "speed_kmh"
            ).alias(
                "vitesse_moyenne_mesures_kmh"
            ),

            F.max(
                "speed_kmh"
            ).alias(
                "vitesse_max_kmh"
            ),

            F.avg(
                "fuelLevel_valide"
            ).alias(
                "fuel_moyen_pct"
            ),
        )
        .withColumn(
            "jour_actif",
            (
                F.col("distance_km")
                >= F.lit(
                    SEUIL_JOUR_ACTIF_KM
                )
            ),
        )
    )

    return kpi_daily


# ============================================================
# KPI DE BASE PAR VEHICULE
# ============================================================

def compute_vehicle_base_kpis_spark(
    df_kpi: DataFrame,
) -> DataFrame:
    """
    KPI principaux sur toute la période,
    par véhicule.
    """

    return (
        df_kpi
        .groupBy(
            "deviceId"
        )
        .agg(
            F.count(
                F.lit(1)
            ).alias(
                "nombre_mesures"
            ),

            F.min(
                "fixTime"
            ).alias(
                "debut_periode"
            ),

            F.max(
                "fixTime"
            ).alias(
                "fin_periode"
            ),

            (
                F.sum(
                    "distance_positive_m"
                )
                / F.lit(1000.0)
            ).alias(
                "distance_km"
            ),

            F.avg(
                "speed_kmh"
            ).alias(
                "vitesse_moyenne_mesures_kmh"
            ),

            F.max(
                "speed_kmh"
            ).alias(
                "vitesse_max_kmh"
            ),

            F.avg(
                "fuelLevel_valide"
            ).alias(
                "fuel_moyen_pct"
            ),

            F.min(
                "fuelLevel_valide"
            ).alias(
                "fuel_min_pct"
            ),

            F.max(
                "fuelLevel_valide"
            ).alias(
                "fuel_max_pct"
            ),
        )
    )


# ============================================================
# VITESSE MOYENNE EN MOUVEMENT
# ============================================================

def add_moving_speed_kpi_spark(
    df_kpi: DataFrame,
    kpi_vehicle: DataFrame,
) -> DataFrame:
    """
    Ajoute la vitesse moyenne lorsque
    speed_kmh > 5.
    """

    moving_speed = (
        df_kpi
        .filter(
            F.col(
                "en_mouvement_kpi"
            )
        )
        .groupBy(
            "deviceId"
        )
        .agg(
            F.avg(
                "speed_kmh"
            ).alias(
                "vitesse_moyenne_en_mouvement_kmh"
            )
        )
    )

    return (
        kpi_vehicle
        .join(
            moving_speed,
            on="deviceId",
            how="left",
        )
    )


# ============================================================
# ACTIVITE ET COUVERTURE
# ============================================================

def add_activity_kpis_spark(
    kpi_vehicle: DataFrame,
    kpi_daily: DataFrame,
) -> DataFrame:
    """
    Ajoute jours avec données, jours actifs,
    distance moyenne par jour actif et couverture.
    """

    days_summary = (
        kpi_daily
        .groupBy(
            "deviceId"
        )
        .agg(
            F.countDistinct(
                "date"
            ).alias(
                "jours_avec_donnees"
            ),

            F.sum(
                F.when(
                    F.col("jour_actif"),
                    F.lit(1),
                ).otherwise(
                    F.lit(0)
                )
            ).alias(
                "jours_actifs"
            ),
        )
    )

    active_distance = (
        kpi_daily
        .filter(
            F.col(
                "jour_actif"
            )
        )
        .groupBy(
            "deviceId"
        )
        .agg(
            F.avg(
                "distance_km"
            ).alias(
                "distance_moyenne_par_jour_actif_km"
            )
        )
    )

    result = (
        kpi_vehicle
        .join(
            days_summary,
            on="deviceId",
            how="left",
        )
        .join(
            active_distance,
            on="deviceId",
            how="left",
        )
    )

    # Nombre de jours calendaires :
    # date(fin) - date(début) + 1
    result = result.withColumn(
        "jours_calendaires_periode",
        (
            F.datediff(
                F.to_date(
                    F.col("fin_periode")
                ),
                F.to_date(
                    F.col("debut_periode")
                ),
            )
            + F.lit(1)
        ),
    )

    result = result.withColumn(
        "taux_couverture_jours_pct",
        (
            F.col(
                "jours_avec_donnees"
            )
            /
            F.col(
                "jours_calendaires_periode"
            )
            *
            F.lit(100.0)
        ),
    )

    return result


# ============================================================
# QUALITE DU SIGNAL fuelLevel
# ============================================================

def add_fuel_quality_kpis_spark(
    df_kpi: DataFrame,
    kpi_vehicle: DataFrame,
) -> DataFrame:
    """
    Compte les fuelLevel hors de 0-100 %.

    Ce sont des incohérences de données,
    pas des anomalies métier.
    """

    quality = (
        df_kpi
        .withColumn(
            "fuel_incoherent",
            F.when(
                F.col(
                    "fuelLevel"
                ).between(
                    0,
                    100,
                ),
                F.lit(0),
            ).otherwise(
                F.lit(1)
            ),
        )
        .groupBy(
            "deviceId"
        )
        .agg(
            F.sum(
                "fuel_incoherent"
            ).alias(
                "nb_incoherences_fuel"
            ),

            F.count(
                F.lit(1)
            ).alias(
                "total_mesures_qualite"
            ),
        )
        .withColumn(
            "pct_incoherences_fuel",
            (
                F.col(
                    "nb_incoherences_fuel"
                )
                /
                F.col(
                    "total_mesures_qualite"
                )
                *
                F.lit(100.0)
            ),
        )
        .drop(
            "total_mesures_qualite"
        )
    )

    return (
        kpi_vehicle
        .join(
            quality,
            on="deviceId",
            how="left",
        )
        .fillna(
            {
                "nb_incoherences_fuel": 0,
            }
        )
    )


# ============================================================
# KPI EVENEMENTS EN PANDAS
# ============================================================

def add_event_kpis_pandas(
    kpi_vehicle: pd.DataFrame,
    refueling_episodes: Optional[
        pd.DataFrame
    ] = None,
    suspicious_events: Optional[
        pd.DataFrame
    ] = None,
) -> pd.DataFrame:
    """
    Les agrégations lourdes sont faites par Spark.

    Les événements sont déjà des tables beaucoup
    plus petites : on les ajoute donc après
    conversion de kpi_vehicle en Pandas.
    """

    result = kpi_vehicle.copy()

    # --------------------------------------------------------
    # Ravitaillements
    # --------------------------------------------------------

    if (
        refueling_episodes is not None
        and not refueling_episodes.empty
    ):

        kpi_refuels = (
            refueling_episodes
            .groupby(
                "deviceId"
            )
            .agg(
                nb_ravitaillements_potentiels=(
                    "refuel_episode_id",
                    "count",
                ),

                hausse_moyenne_refuel_pct=(
                    "total_delta_fuel_pct",
                    "mean",
                ),

                hausse_max_refuel_pct=(
                    "total_delta_fuel_pct",
                    "max",
                ),
            )
            .reset_index()
        )

        result = result.merge(
            kpi_refuels,
            on="deviceId",
            how="left",
        )

    else:

        result[
            "nb_ravitaillements_potentiels"
        ] = 0

        result[
            "hausse_moyenne_refuel_pct"
        ] = pd.NA

        result[
            "hausse_max_refuel_pct"
        ] = pd.NA

    # --------------------------------------------------------
    # Baisses suspectes
    # --------------------------------------------------------

    if (
        suspicious_events is not None
        and not suspicious_events.empty
    ):

        kpi_suspicious = (
            suspicious_events
            .groupby(
                "deviceId"
            )
            .agg(
                nb_baisses_suspectes=(
                    "suspicious_event_id",
                    "count",
                ),

                baisse_moyenne_suspecte_pct=(
                    "drop_abs_pct",
                    "mean",
                ),

                baisse_max_suspecte_pct=(
                    "drop_abs_pct",
                    "max",
                ),
            )
            .reset_index()
        )

        result = result.merge(
            kpi_suspicious,
            on="deviceId",
            how="left",
        )

    else:

        result[
            "nb_baisses_suspectes"
        ] = 0

        result[
            "baisse_moyenne_suspecte_pct"
        ] = pd.NA

        result[
            "baisse_max_suspecte_pct"
        ] = pd.NA

    # --------------------------------------------------------
    # Compteurs à zéro si absence d'événement
    # --------------------------------------------------------

    result[
        "nb_ravitaillements_potentiels"
    ] = (
        result[
            "nb_ravitaillements_potentiels"
        ]
        .fillna(0)
        .astype(int)
    )

    result[
        "nb_baisses_suspectes"
    ] = (
        result[
            "nb_baisses_suspectes"
        ]
        .fillna(0)
        .astype(int)
    )

    return result


# ============================================================
# KPI GLOBAUX
# ============================================================

def compute_global_kpis_spark(
    df_kpi: DataFrame,
    kpi_vehicle: pd.DataFrame,
) -> Dict:
    """
    KPI principaux de toute la flotte.
    """

    nombre_vehicules = (
        df_kpi
        .select(
            "deviceId"
        )
        .distinct()
        .count()
    )

    nombre_total_mesures = (
        df_kpi.count()
    )

    return {
        "nombre_vehicules":
            int(
                nombre_vehicules
            ),

        "nombre_total_mesures":
            int(
                nombre_total_mesures
            ),

        "distance_totale_km":
            round(
                float(
                    kpi_vehicle[
                        "distance_km"
                    ].sum()
                ),
                2,
            ),

        "nb_ravitaillements_potentiels":
            int(
                kpi_vehicle[
                    "nb_ravitaillements_potentiels"
                ].sum()
            ),

        "nb_baisses_suspectes":
            int(
                kpi_vehicle[
                    "nb_baisses_suspectes"
                ].sum()
            ),

        "nb_incoherences_fuel":
            int(
                kpi_vehicle[
                    "nb_incoherences_fuel"
                ].sum()
            ),
    }


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def compute_fleet_kpis_spark(
    df_prepared: DataFrame,
    refueling_episodes: Optional[
        pd.DataFrame
    ] = None,
    suspicious_events: Optional[
        pd.DataFrame
    ] = None,
) -> Dict:
    """
    Version Spark de compute_fleet_kpis().

    Les millions de mesures restent dans Spark.

    Seules les petites tables agrégées sont
    converties en Pandas pour rester compatibles
    avec le reste de la plateforme.
    """

    # --------------------------------------------------------
    # 1. Préparation
    # --------------------------------------------------------

    df_kpi = (
        prepare_kpi_data_spark(
            df_prepared
        )
    )

    # --------------------------------------------------------
    # 2. KPI journaliers
    # --------------------------------------------------------

    kpi_daily_spark = (
        compute_daily_kpis_spark(
            df_kpi
        )
    )

    # --------------------------------------------------------
    # 3. KPI de base
    # --------------------------------------------------------

    kpi_vehicle_spark = (
        compute_vehicle_base_kpis_spark(
            df_kpi
        )
    )

    # --------------------------------------------------------
    # 4. Vitesse en mouvement
    # --------------------------------------------------------

    kpi_vehicle_spark = (
        add_moving_speed_kpi_spark(
            df_kpi,
            kpi_vehicle_spark,
        )
    )

    # --------------------------------------------------------
    # 5. Activité / couverture
    # --------------------------------------------------------

    kpi_vehicle_spark = (
        add_activity_kpis_spark(
            kpi_vehicle_spark,
            kpi_daily_spark,
        )
    )

    # --------------------------------------------------------
    # 6. Qualité carburant
    # --------------------------------------------------------

    kpi_vehicle_spark = (
        add_fuel_quality_kpis_spark(
            df_kpi,
            kpi_vehicle_spark,
        )
    )

    # --------------------------------------------------------
    # 7. Conversion des petites tables uniquement
    # --------------------------------------------------------

    kpi_daily = (
        kpi_daily_spark
        .orderBy(
            "deviceId",
            "date",
        )
        .toPandas()
    )

    kpi_vehicle = (
        kpi_vehicle_spark
        .orderBy(
            "deviceId"
        )
        .toPandas()
    )

    # --------------------------------------------------------
    # 8. Evénements
    # --------------------------------------------------------

    kpi_vehicle = (
        add_event_kpis_pandas(
            kpi_vehicle,
            refueling_episodes,
            suspicious_events,
        )
    )

    # --------------------------------------------------------
    # 9. Types des compteurs
    # --------------------------------------------------------

    integer_columns = [
        "nombre_mesures",
        "jours_calendaires_periode",
        "jours_avec_donnees",
        "jours_actifs",
        "nb_ravitaillements_potentiels",
        "nb_baisses_suspectes",
        "nb_incoherences_fuel",
    ]

    for column in integer_columns:

        if column in kpi_vehicle.columns:

            kpi_vehicle[
                column
            ] = (
                pd.to_numeric(
                    kpi_vehicle[
                        column
                    ],
                    errors="coerce",
                )
                .fillna(0)
                .astype(int)
            )

    # --------------------------------------------------------
    # 10. Ordre final identique au pipeline Pandas
    # --------------------------------------------------------

    kpi_vehicle = (
        kpi_vehicle[
            KPI_VEHICLE_COLUMNS
        ]
    )

    # --------------------------------------------------------
    # 11. KPI globaux
    # --------------------------------------------------------

    kpi_global = (
        compute_global_kpis_spark(
            df_kpi,
            kpi_vehicle,
        )
    )

    return {
        "df_kpi":
            df_kpi,

        "kpi_daily":
            kpi_daily,

        "kpi_vehicle":
            kpi_vehicle,

        "kpi_global":
            kpi_global,
    }