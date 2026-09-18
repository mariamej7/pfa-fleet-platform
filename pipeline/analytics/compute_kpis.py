from typing import Dict, Optional

import pandas as pd


# ============================================================
# SEUILS KPI
# ============================================================

# Même seuil que dans le Notebook 2 :
# utilisé uniquement pour calculer
# la vitesse moyenne en mouvement.
SEUIL_MOUVEMENT_KPI_KMH = 5

# Un jour est considéré actif
# si au moins 1 km est parcouru.
SEUIL_JOUR_ACTIF_KM = 1


# ============================================================
# PREPARATION DES VARIABLES KPI
# ============================================================

def prepare_kpi_data(
    df_prepared: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prépare les variables nécessaires
    au calcul des KPI.

    Le DataFrame reçu doit provenir
    de preprocessing/prepare_data.py.
    """

    df_kpi = df_prepared.copy()

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
        if column not in df_kpi.columns
    ]

    if missing_columns:
        raise ValueError(
            "Impossible de calculer les KPI. "
            f"Colonnes manquantes : {missing_columns}"
        )

    # --------------------------------------------------------
    # Types
    # --------------------------------------------------------

    df_kpi["fixTime"] = pd.to_datetime(
        df_kpi["fixTime"],
        format="mixed",
        errors="coerce",
    )

    colonnes_numeriques = [
        "speed_kmh",
        "fuelLevel",
        "odometer",
        "delta_odometer_m",
    ]

    for column in colonnes_numeriques:
        df_kpi[column] = pd.to_numeric(
            df_kpi[column],
            errors="coerce",
        )

    # --------------------------------------------------------
    # fuelLevel valide pour les statistiques
    #
    # Les valeurs hors 0-100 % restent dans
    # les données, mais sont exclues des
    # moyennes/min/max de carburant.
    # --------------------------------------------------------

    df_kpi["fuelLevel_valide"] = (
        df_kpi["fuelLevel"]
        .where(
            df_kpi["fuelLevel"].between(
                0,
                100,
            )
        )
    )

    # --------------------------------------------------------
    # Distance
    #
    # On ne somme que les variations
    # positives de l'odomètre.
    # --------------------------------------------------------

    df_kpi["distance_positive_m"] = (
        df_kpi["delta_odometer_m"]
        .clip(lower=0)
    )

    # --------------------------------------------------------
    # Véhicule en mouvement
    # --------------------------------------------------------

    df_kpi["en_mouvement_kpi"] = (
        df_kpi["speed_kmh"]
        > SEUIL_MOUVEMENT_KPI_KMH
    )

    # Date sans l'heure
    df_kpi["date"] = (
        df_kpi["fixTime"].dt.date
    )

    return df_kpi


# ============================================================
# KPI JOURNALIERS
# ============================================================

def compute_daily_kpis(
    df_kpi: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcule une ligne par véhicule et par jour.
    """

    kpi_daily = (
        df_kpi
        .dropna(subset=["date"])
        .groupby(
            [
                "deviceId",
                "date",
            ],
            as_index=False,
        )
        .agg(
            nombre_mesures=(
                "deviceId",
                "size",
            ),

            distance_km=(
                "distance_positive_m",
                lambda values:
                    values.sum() / 1000,
            ),

            vitesse_moyenne_mesures_kmh=(
                "speed_kmh",
                "mean",
            ),

            vitesse_max_kmh=(
                "speed_kmh",
                "max",
            ),

            fuel_moyen_pct=(
                "fuelLevel_valide",
                "mean",
            ),
        )
    )

    # Jour avec au moins 1 km parcouru
    kpi_daily["jour_actif"] = (
        kpi_daily["distance_km"]
        >= SEUIL_JOUR_ACTIF_KM
    )

    return kpi_daily


# ============================================================
# KPI DE BASE PAR VEHICULE
# ============================================================

def compute_vehicle_base_kpis(
    df_kpi: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcule les principaux KPI
    sur toute la période pour chaque véhicule.
    """

    kpi_base = (
        df_kpi
        .groupby("deviceId")
        .agg(
            nombre_mesures=(
                "deviceId",
                "size",
            ),

            debut_periode=(
                "fixTime",
                "min",
            ),

            fin_periode=(
                "fixTime",
                "max",
            ),

            distance_km=(
                "distance_positive_m",
                lambda values:
                    values.sum() / 1000,
            ),

            vitesse_moyenne_mesures_kmh=(
                "speed_kmh",
                "mean",
            ),

            vitesse_max_kmh=(
                "speed_kmh",
                "max",
            ),

            fuel_moyen_pct=(
                "fuelLevel_valide",
                "mean",
            ),

            fuel_min_pct=(
                "fuelLevel_valide",
                "min",
            ),

            fuel_max_pct=(
                "fuelLevel_valide",
                "max",
            ),
        )
        .reset_index()
    )

    return kpi_base


# ============================================================
# VITESSE MOYENNE EN MOUVEMENT
# ============================================================

def add_moving_speed_kpi(
    df_kpi: pd.DataFrame,
    kpi_vehicle: pd.DataFrame,
) -> pd.DataFrame:

    vitesse_mouvement = (
        df_kpi[
            df_kpi["en_mouvement_kpi"]
        ]
        .groupby("deviceId")[
            "speed_kmh"
        ]
        .mean()
        .rename(
            "vitesse_moyenne_en_mouvement_kmh"
        )
        .reset_index()
    )

    return kpi_vehicle.merge(
        vitesse_mouvement,
        on="deviceId",
        how="left",
    )


# ============================================================
# ACTIVITE ET COUVERTURE
# ============================================================

def add_activity_kpis(
    kpi_vehicle: pd.DataFrame,
    kpi_daily: pd.DataFrame,
) -> pd.DataFrame:

    resume_jours = (
        kpi_daily
        .groupby("deviceId")
        .agg(
            jours_avec_donnees=(
                "date",
                "nunique",
            ),

            jours_actifs=(
                "jour_actif",
                "sum",
            ),
        )
        .reset_index()
    )

    # Distance moyenne uniquement
    # pendant les jours actifs.
    distance_jour_actif = (
        kpi_daily[
            kpi_daily["jour_actif"]
        ]
        .groupby("deviceId")[
            "distance_km"
        ]
        .mean()
        .rename(
            "distance_moyenne_par_jour_actif_km"
        )
        .reset_index()
    )

    resume_jours = resume_jours.merge(
        distance_jour_actif,
        on="deviceId",
        how="left",
    )

    kpi_vehicle = kpi_vehicle.merge(
        resume_jours,
        on="deviceId",
        how="left",
    )

    # Nombre de jours calendaires
    # entre le début et la fin de la période.
    kpi_vehicle[
        "jours_calendaires_periode"
    ] = (
        (
            kpi_vehicle[
                "fin_periode"
            ].dt.normalize()
            -
            kpi_vehicle[
                "debut_periode"
            ].dt.normalize()
        ).dt.days
        + 1
    )

    kpi_vehicle[
        "taux_couverture_jours_pct"
    ] = (
        kpi_vehicle[
            "jours_avec_donnees"
        ]
        /
        kpi_vehicle[
            "jours_calendaires_periode"
        ]
        * 100
    )

    return kpi_vehicle


# ============================================================
# QUALITE DU SIGNAL fuelLevel
# ============================================================

def add_fuel_quality_kpis(
    df_kpi: pd.DataFrame,
    kpi_vehicle: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compte les fuelLevel hors de la plage 0-100 %.

    Ce sont des incohérences de données,
    pas des anomalies métier.
    """

    df_quality = df_kpi.copy()

    df_quality["fuel_incoherent"] = (
        ~df_quality["fuelLevel"].between(
            0,
            100,
        )
    )

    kpi_quality = (
        df_quality
        .groupby("deviceId")
        .agg(
            nb_incoherences_fuel=(
                "fuel_incoherent",
                "sum",
            ),

            total_mesures_qualite=(
                "deviceId",
                "size",
            ),
        )
        .reset_index()
    )

    kpi_quality[
        "pct_incoherences_fuel"
    ] = (
        kpi_quality[
            "nb_incoherences_fuel"
        ]
        /
        kpi_quality[
            "total_mesures_qualite"
        ]
        * 100
    )

    kpi_vehicle = kpi_vehicle.merge(
        kpi_quality[
            [
                "deviceId",
                "nb_incoherences_fuel",
                "pct_incoherences_fuel",
            ]
        ],
        on="deviceId",
        how="left",
    )

    kpi_vehicle[
        "nb_incoherences_fuel"
    ] = (
        kpi_vehicle[
            "nb_incoherences_fuel"
        ]
        .fillna(0)
        .astype(int)
    )

    return kpi_vehicle


# ============================================================
# KPI EVENEMENTS
#
# Ces deux tables seront produites plus tard
# par anomaly_detection/.
# ============================================================

def add_event_kpis(
    kpi_vehicle: pd.DataFrame,
    refueling_episodes: Optional[
        pd.DataFrame
    ] = None,
    suspicious_events: Optional[
        pd.DataFrame
    ] = None,
) -> pd.DataFrame:
    """
    Ajoute les KPI liés aux événements carburant.

    Les DataFrames sont optionnels pour permettre
    de tester les KPI de performance avant
    l'industrialisation des règles de détection.
    """

    result = kpi_vehicle.copy()

    # --------------------------------------------------------
    # Ravitaillements potentiels
    # --------------------------------------------------------

    if (
        refueling_episodes is not None
        and not refueling_episodes.empty
    ):
        kpi_refuels = (
            refueling_episodes
            .groupby("deviceId")
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
            .groupby("deviceId")
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

    # Les véhicules sans événement
    # doivent avoir un compteur égal à zéro.
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

def compute_global_kpis(
    df_kpi: pd.DataFrame,
    kpi_vehicle: pd.DataFrame,
) -> Dict:
    """
    KPI principaux de toute la flotte.
    """

    return {
        "nombre_vehicules":
            int(
                df_kpi[
                    "deviceId"
                ].nunique()
            ),

        "nombre_total_mesures":
            int(len(df_kpi)),

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

def compute_fleet_kpis(
    df_prepared: pd.DataFrame,
    refueling_episodes: Optional[
        pd.DataFrame
    ] = None,
    suspicious_events: Optional[
        pd.DataFrame
    ] = None,
) -> Dict:
    """
    Fonction principale du module KPI.

    Retourne :
    - les données préparées pour KPI ;
    - les KPI journaliers ;
    - les KPI par véhicule ;
    - les KPI globaux.
    """

    # 1. Variables nécessaires
    df_kpi = prepare_kpi_data(
        df_prepared
    )

    # 2. KPI journaliers
    kpi_daily = compute_daily_kpis(
        df_kpi
    )

    # 3. KPI de base
    kpi_vehicle = (
        compute_vehicle_base_kpis(
            df_kpi
        )
    )

    # 4. Vitesse en mouvement
    kpi_vehicle = (
        add_moving_speed_kpi(
            df_kpi,
            kpi_vehicle,
        )
    )

    # 5. Activité / couverture
    kpi_vehicle = add_activity_kpis(
        kpi_vehicle,
        kpi_daily,
    )

    # 6. Qualité fuelLevel
    kpi_vehicle = (
        add_fuel_quality_kpis(
            df_kpi,
            kpi_vehicle,
        )
    )

    # 7. Événements carburant
    #
    # Pour l'instant, si les tables de détection
    # ne sont pas encore disponibles,
    # les compteurs restent à zéro.
    kpi_vehicle = add_event_kpis(
        kpi_vehicle,
        refueling_episodes,
        suspicious_events,
    )

    # --------------------------------------------------------
    # Ordre final des colonnes
    # --------------------------------------------------------

    final_columns = [
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

    kpi_vehicle = kpi_vehicle[
        final_columns
    ]

    kpi_global = compute_global_kpis(
        df_kpi,
        kpi_vehicle,
    )

    return {
        "df_kpi": df_kpi,
        "kpi_daily": kpi_daily,
        "kpi_vehicle": kpi_vehicle,
        "kpi_global": kpi_global,
    }