from datetime import datetime
from typing import Dict
from uuid import uuid4

import pandas as pd
from sqlalchemy import text

from app.core.database import engine


# ============================================================
# COLONNES ATTENDUES PAR POSTGRESQL
# ============================================================

TABLE_COLUMNS = {

    "dim_vehicles": [
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
        "nb_baisses_analysees",
        "nb_candidats_ia",
        "nb_alertes_regles",
        "nb_overlap_regles_ia",
        "nb_alertes_ia_uniquement",
        "nb_alertes_regle_uniquement",
    ],

    "fact_fleet_daily": [
        "deviceId",
        "date",
        "nombre_mesures",
        "distance_km",
        "vitesse_moyenne_mesures_kmh",
        "vitesse_max_kmh",
        "fuel_moyen_pct",
        "jour_actif",
        "annee",
        "mois",
        "jour_semaine",
        "mois_annee",
    ],

    "fact_refueling_events": [
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
    ],

    "fact_fuel_alerts": [
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
    ],

    "fact_fuel_events": [
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
    ],

    "fleet_summary": [
        "date_generation",
        "nombre_vehicules",
        "nombre_total_mesures",
        "distance_totale_km",
        "nb_ravitaillements_potentiels",
        "nb_alertes_regles",
        "nb_candidats_ia",
        "nb_regle_et_ia",
        "nb_alertes_finales_uniques",
        "nb_alertes_p1_critiques",
        "nb_incoherences_fuel",
    ],
}


# ============================================================
# PREPARER UN DATAFRAME POUR POSTGRESQL
# ============================================================

def _prepare_dataframe(
    dataframe: pd.DataFrame,
    table_name: str,
) -> pd.DataFrame:

    if not isinstance(dataframe, pd.DataFrame):
        raise ValueError(
            f"{table_name} n'est pas un DataFrame."
        )

    expected_columns = TABLE_COLUMNS[
        table_name
    ]

    missing_columns = [
        column
        for column in expected_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            (
                f"Colonnes manquantes pour "
                f"{table_name} : "
                f"{missing_columns}"
            )
        )

    # On conserve uniquement les colonnes
    # réellement présentes dans PostgreSQL.
    result = dataframe[
        expected_columns
    ].copy()

    # PostgreSQL utilise ici des TIMESTAMP sans timezone.
    # Si Pandas contient une timezone, on la convertit
    # en UTC puis on retire l'information de timezone.
    for column in result.columns:

        dtype = result[column].dtype

        if isinstance(
            dtype,
            pd.DatetimeTZDtype,
        ):

            result[column] = (
                result[column]
                .dt.tz_convert("UTC")
                .dt.tz_localize(None)
            )

    return result


# ============================================================
# CREER UN RUN D'ANALYSE
# ============================================================

def create_analysis_run(
    upload_id: str,
    filename: str,
) -> str:

    analysis_run_id = uuid4().hex

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                INSERT INTO analysis_runs (
                    analysis_run_id,
                    upload_id,
                    filename,
                    status,
                    created_at,
                    completed_at,
                    is_active,
                    nombre_lignes_preparees,
                    nombre_vehicules,
                    nombre_alertes_finales,
                    error_message
                )
                VALUES (
                    :analysis_run_id,
                    :upload_id,
                    :filename,
                    'processing',
                    :created_at,
                    NULL,
                    FALSE,
                    NULL,
                    NULL,
                    NULL,
                    NULL
                )
                """
            ),
            {
                "analysis_run_id":
                    analysis_run_id,
                "upload_id":
                    upload_id,
                "filename":
                    filename,
                "created_at":
                    datetime.now(),
            },
        )

    return analysis_run_id


# ============================================================
# MARQUER UN RUN COMME ECHOUE
# ============================================================

def mark_analysis_run_failed(
    analysis_run_id: str,
    error_message: str,
) -> None:

    # Limiter la taille du message enregistré.
    safe_message = str(
        error_message
    )[:4000]

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE analysis_runs
                SET
                    status = 'failed',
                    completed_at = :completed_at,
                    is_active = FALSE,
                    error_message = :error_message
                WHERE analysis_run_id = :analysis_run_id
                """
            ),
            {
                "analysis_run_id":
                    analysis_run_id,
                "completed_at":
                    datetime.now(),
                "error_message":
                    safe_message,
            },
        )


# ============================================================
# ENREGISTRER LES TABLES DU PIPELINE
# ============================================================

def save_platform_results(
    analysis_run_id: str,
    platform_results: Dict,
) -> Dict:

    """
    Remplace les données actuellement affichées
    dans les 6 tables PostgreSQL par celles du
    nouveau dataset.

    Tout est exécuté dans UNE transaction.

    Si une erreur apparaît :
    - PostgreSQL annule les suppressions ;
    - les anciennes données restent disponibles ;
    - le nouveau run n'est pas activé.
    """

    prepared_tables = {}

    for table_name in TABLE_COLUMNS:

        if table_name not in platform_results:

            raise ValueError(
                (
                    "Table absente des résultats "
                    f"du pipeline : {table_name}"
                )
            )

        prepared_tables[
            table_name
        ] = _prepare_dataframe(
            platform_results[
                table_name
            ],
            table_name,
        )


    # --------------------------------------------------------
    # INFORMATIONS DU RUN
    # --------------------------------------------------------

    nombre_vehicules = len(
        prepared_tables[
            "dim_vehicles"
        ]
    )

    nombre_alertes = len(
        prepared_tables[
            "fact_fuel_alerts"
        ]
    )

    if (
        prepared_tables[
            "fleet_summary"
        ].empty
    ):

        nombre_mesures = 0

    else:

        nombre_mesures_value = (
            prepared_tables[
                "fleet_summary"
            ]
            .iloc[0][
                "nombre_total_mesures"
            ]
        )

        nombre_mesures = (
            int(nombre_mesures_value)
            if pd.notna(
                nombre_mesures_value
            )
            else 0
        )


    # ========================================================
    # TRANSACTION POSTGRESQL
    # ========================================================

    with engine.begin() as connection:

        # ----------------------------------------------------
        # 1. SUPPRIMER L'ANCIEN DATASET ACTIF
        # ----------------------------------------------------
        #
        # Les tables enfants sont supprimées avant
        # dim_vehicles à cause des clés étrangères.

        connection.execute(
            text(
                "DELETE FROM fact_fuel_events"
            )
        )

        connection.execute(
            text(
                "DELETE FROM fact_fuel_alerts"
            )
        )

        connection.execute(
            text(
                "DELETE FROM fact_refueling_events"
            )
        )

        connection.execute(
            text(
                "DELETE FROM fact_fleet_daily"
            )
        )

        connection.execute(
            text(
                "DELETE FROM fleet_summary"
            )
        )

        connection.execute(
            text(
                "DELETE FROM dim_vehicles"
            )
        )


        # ----------------------------------------------------
        # 2. INSERER LE NOUVEAU DATASET
        # ----------------------------------------------------

        insert_order = [
            "dim_vehicles",
            "fact_fleet_daily",
            "fact_refueling_events",
            "fact_fuel_alerts",
            "fact_fuel_events",
            "fleet_summary",
        ]

        for table_name in insert_order:

            dataframe = prepared_tables[
                table_name
            ]

            # Permet de gérer proprement un dataset
            # qui ne contient, par exemple,
            # aucun ravitaillement ou aucune alerte.
            if dataframe.empty:
                continue

            dataframe.to_sql(
                name=table_name,
                con=connection,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000,
            )


        # ----------------------------------------------------
        # 3. DESACTIVER L'ANCIEN RUN
        # ----------------------------------------------------

        connection.execute(
            text(
                """
                UPDATE analysis_runs
                SET is_active = FALSE
                WHERE
                    is_active = TRUE
                    AND analysis_run_id
                        <> :analysis_run_id
                """
            ),
            {
                "analysis_run_id":
                    analysis_run_id,
            },
        )


        # ----------------------------------------------------
        # 4. ACTIVER LE NOUVEAU RUN
        # ----------------------------------------------------

        connection.execute(
            text(
                """
                UPDATE analysis_runs
                SET
                    status = 'completed',
                    completed_at = :completed_at,
                    is_active = TRUE,
                    nombre_lignes_preparees =
                        :nombre_lignes_preparees,
                    nombre_vehicules =
                        :nombre_vehicules,
                    nombre_alertes_finales =
                        :nombre_alertes_finales,
                    error_message = NULL
                WHERE analysis_run_id =
                    :analysis_run_id
                """
            ),
            {
                "analysis_run_id":
                    analysis_run_id,

                "completed_at":
                    datetime.now(),

                "nombre_lignes_preparees":
                    nombre_mesures,

                "nombre_vehicules":
                    nombre_vehicules,

                "nombre_alertes_finales":
                    nombre_alertes,
            },
        )


    # ========================================================
    # RESULTAT
    # ========================================================

    return {
        "analysis_run_id":
            analysis_run_id,

        "database_saved":
            True,

        "nombre_vehicules":
            nombre_vehicules,

        "nombre_lignes_preparees":
            nombre_mesures,

        "nombre_alertes_finales":
            nombre_alertes,

        "tables": {
            table_name:
                len(dataframe)

            for (
                table_name,
                dataframe,
            ) in prepared_tables.items()
        },
    }