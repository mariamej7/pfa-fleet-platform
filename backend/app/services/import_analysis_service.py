import math
import os
import re
import sys
from pathlib import Path
from typing import Dict
from uuid import uuid4

import pandas as pd


PANDAS_WEB_SAMPLE_ROWS = max(
    10_000,
    int(
        os.getenv(
            "IMPORT_PANDAS_SAMPLE_ROWS",
            "80000",
        )
    ),
)


# ============================================================
# CHEMINS DU PROJET
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

PIPELINE_DIR = PROJECT_ROOT / "pipeline"

if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(PIPELINE_DIR),
    )


# ============================================================
# PIPELINE PANDAS
# ============================================================

from preprocessing.prepare_data import (  # noqa: E402
    prepare_fleet_data,
)

from anomaly_detection.rule_detection import (  # noqa: E402
    detect_rule_events,
)

from anomaly_detection.context_analysis import (  # noqa: E402
    analyze_suspicious_context,
)

from anomaly_detection.isolation_forest import (  # noqa: E402
    detect_ai_anomalies,
)

from analytics.compute_kpis import (  # noqa: E402
    compute_fleet_kpis,
)


# ============================================================
# PIPELINE SPARK
# ============================================================

from big_data.spark_processing import (  # noqa: E402
    create_spark_session,
    load_telemetry_spark,
    prepare_telemetry_spark,
)

from big_data.spark_rule_detection import (  # noqa: E402
    detect_rule_events_spark,
)

from big_data.spark_context_analysis import (  # noqa: E402
    analyze_suspicious_context_spark,
)

from big_data.spark_ai_detection import (  # noqa: E402
    detect_ai_anomalies_spark,
)

from big_data.spark_kpis import (  # noqa: E402
    compute_fleet_kpis_spark,
)


# ============================================================
# TABLES PLATEFORME
# ============================================================

from platform_tables.prepare_platform_tables import (  # noqa: E402
    prepare_platform_tables,
)


# ============================================================
# VALIDATION / CHOIX DU MOTEUR
# ============================================================

from app.services.import_validation_service import (
    load_validation_metadata,
)


# ============================================================
# POSTGRESQL
# ============================================================

from app.services.database_persistence_service import (
    create_analysis_run,
    mark_analysis_run_failed,
    save_platform_results,
)


# ============================================================
# TROUVER LE FICHIER IMPORTE
# ============================================================

def find_uploaded_file(
    upload_dir: Path,
    upload_id: str,
) -> Path:
    """
    Retrouve le fichier CSV ou Parquet
    correspondant à un upload_id.
    """

    if not re.fullmatch(
        r"[0-9a-fA-F]{32}",
        upload_id,
    ):
        raise ValueError(
            "Identifiant d'import invalide."
        )

    possible_files = [
        upload_dir / f"{upload_id}.csv",
        upload_dir / f"{upload_id}.parquet",
    ]

    for file_path in possible_files:

        if file_path.exists():
            return file_path

    raise FileNotFoundError(
        (
            "Aucun fichier importé trouvé "
            f"pour l'identifiant {upload_id}."
        )
    )


# ============================================================
# COMPTER UNE VALEUR
# ============================================================

def _count_value(
    dataframe: pd.DataFrame,
    column: str,
    value,
) -> int:
    """
    Compte une valeur dans une colonne seulement
    lorsque la table et la colonne existent.
    """

    if dataframe is None:
        return 0

    if dataframe.empty:
        return 0

    if column not in dataframe.columns:
        return 0

    return int(
        (
            dataframe[column]
            == value
        ).sum()
    )


# ============================================================
# CHOIX DU MOTEUR
# ============================================================

def _resolve_processing_engine(
    upload_dir: Path,
    upload_id: str,
) -> Dict:
    """
    Lit le résultat de validation et récupère
    le moteur automatiquement recommandé.

    La validation doit donc avoir lieu avant
    l'analyse.
    """

    metadata = load_validation_metadata(
        upload_dir,
        upload_id,
    )

    if metadata is None:

        raise ValueError(
            (
                "Le fichier doit être validé "
                "avant de lancer l'analyse."
            )
        )

    if not metadata.get(
        "compatible",
        False,
    ):

        raise ValueError(
            (
                "Le fichier n'est pas compatible "
                "avec le pipeline d'analyse."
            )
        )

    engine_code = metadata.get(
        "moteur_recommande"
    )

    if engine_code not in {
        "pandas",
        "spark",
    }:

        raise ValueError(
            (
                "Aucun moteur de traitement valide "
                "n'a été déterminé. "
                "Veuillez revalider le fichier."
            )
        )

    if engine_code == "spark":

        default_label = (
            "Apache Spark"
        )

    else:

        default_label = (
            "Pandas"
        )

    return {
        "code":
            engine_code,

        "label":
            metadata.get(
                "moteur_libelle"
            )
            or default_label,

        "reason":
            metadata.get(
                "raison_moteur"
            ),

        "row_count":
            metadata.get(
                "nombre_lignes"
            ),

        "spark_threshold":
            metadata.get(
                "seuil_spark_lignes"
            ),
    }


# ============================================================
# ECHANTILLON WEB PANDAS
# ============================================================

def _prepare_pandas_analysis_file(
    file_path: Path,
    source_row_count: int,
) -> tuple[Path, Dict]:
    """
    Conserve toute la période du fichier, mais réduit le nombre
    de lignes analysées sur Render Free pour éviter un dépassement
    de mémoire pendant les copies intermédiaires du pipeline Pandas.
    """

    normalized_row_count = max(
        0,
        int(source_row_count or 0),
    )

    sampling_info = {
        "applied": False,
        "source_rows": normalized_row_count,
        "analyzed_rows": normalized_row_count,
        "step": 1,
        "target_rows": PANDAS_WEB_SAMPLE_ROWS,
    }

    if (
        normalized_row_count
        <= PANDAS_WEB_SAMPLE_ROWS
    ):
        return file_path, sampling_info

    step = max(
        2,
        math.ceil(
            normalized_row_count
            / PANDAS_WEB_SAMPLE_ROWS
        ),
    )

    sample_path = file_path.with_name(
        (
            f"{file_path.stem}"
            ".analysis-sample"
            f"{file_path.suffix.lower()}"
        )
    )

    if file_path.suffix.lower() == ".csv":
        sampled_dataframe = pd.read_csv(
            file_path,
            skiprows=lambda row_index: (
                row_index > 0
                and (row_index - 1) % step != 0
            ),
        )

    elif file_path.suffix.lower() == ".parquet":
        sampled_dataframe = (
            pd.read_parquet(file_path)
            .iloc[::step]
            .copy()
        )

    else:
        raise ValueError(
            "Format de fichier non supporté."
        )

    sampled_dataframe = (
        sampled_dataframe
        .head(PANDAS_WEB_SAMPLE_ROWS)
        .copy()
    )

    if sample_path.suffix == ".csv":
        sampled_dataframe.to_csv(
            sample_path,
            index=False,
        )
    else:
        sampled_dataframe.to_parquet(
            sample_path,
            index=False,
        )

    sampling_info.update(
        {
            "applied": True,
            "analyzed_rows": int(
                len(sampled_dataframe)
            ),
            "step": step,
        }
    )

    return sample_path, sampling_info


# ============================================================
# PIPELINE PANDAS COMPLET
# ============================================================

def _run_pandas_pipeline(
    file_path: Path,
) -> Dict:
    """
    Exécute la chaîne analytique historique Pandas.
    """

    # --------------------------------------------------------
    # Préparation
    # --------------------------------------------------------

    df_prepared, preparation_report = (
        prepare_fleet_data(
            file_path
        )
    )

    # --------------------------------------------------------
    # Règles
    # --------------------------------------------------------

    rule_results = detect_rule_events(
        df_prepared
    )

    df_rules = rule_results[
        "df_rules"
    ]

    refueling_episodes = rule_results[
        "refueling_episodes"
    ]

    suspicious_events = rule_results[
        "suspicious_events"
    ]

    # --------------------------------------------------------
    # Contexte
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Isolation Forest
    # --------------------------------------------------------

    ai_results = detect_ai_anomalies(
        df_rules,
        suspicious_events,
    )

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    kpi_results = compute_fleet_kpis(
        df_rules,
        refueling_episodes=
            refueling_episodes,
        suspicious_events=
            suspicious_events,
    )

    return {
        "preparation_report":
            preparation_report,

        "refueling_episodes":
            refueling_episodes,

        "suspicious_events":
            suspicious_events,

        "suspicious_events_analyzed":
            suspicious_events_analyzed,

        "ai_results":
            ai_results,

        "kpi_results":
            kpi_results,
    }


# ============================================================
# PIPELINE SPARK COMPLET
# ============================================================

def _run_spark_pipeline(
    file_path: Path,
    spark,
) -> Dict:
    """
    Exécute le pipeline gros volume.

    Spark conserve les gros volumes.

    Pandas / Scikit-learn ne reçoivent que
    les petites tables nécessaires au contexte
    et à Isolation Forest.
    """

    df_prepared = None
    df_rules = None

    try:

        # ----------------------------------------------------
        # Lecture Spark
        # ----------------------------------------------------

        df_raw = load_telemetry_spark(
            file_path,
            spark,
        )

        # ----------------------------------------------------
        # Préparation Spark
        # ----------------------------------------------------

        (
            df_prepared,
            preparation_report,
        ) = prepare_telemetry_spark(
            df_raw
        )

        # Cache :
        # plusieurs étapes réutilisent ce dataset.
        df_prepared = (
            df_prepared.cache()
        )

        df_prepared.count()

        # ----------------------------------------------------
        # Règles Spark
        # ----------------------------------------------------

        rule_results = (
            detect_rule_events_spark(
                df_prepared
            )
        )

        df_rules = (
            rule_results[
                "df_rules"
            ]
            .cache()
        )

        df_rules.count()

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

        # ----------------------------------------------------
        # Contexte
        #
        # Spark sélectionne uniquement les fenêtres
        # +/- 30 minutes, puis Pandas applique
        # l'analyse contextuelle existante.
        # ----------------------------------------------------

        context_results = (
            analyze_suspicious_context_spark(
                df_rules,
                suspicious_events,
            )
        )

        suspicious_events_analyzed = (
            context_results[
                "suspicious_events_analyzed"
            ]
        )

        # ----------------------------------------------------
        # Isolation Forest
        #
        # Spark filtre les baisses valides.
        # Seul le sous-ensemble réduit est envoyé
        # vers Pandas / Scikit-learn.
        # ----------------------------------------------------

        ai_results = (
            detect_ai_anomalies_spark(
                df_rules,
                suspicious_events,
            )
        )

        # ----------------------------------------------------
        # KPI Spark
        # ----------------------------------------------------

        kpi_results = (
            compute_fleet_kpis_spark(
                df_rules,
                refueling_episodes=
                    refueling_episodes,
                suspicious_events=
                    suspicious_events,
            )
        )

        return {
            "preparation_report":
                preparation_report,

            "refueling_episodes":
                refueling_episodes,

            "suspicious_events":
                suspicious_events,

            "suspicious_events_analyzed":
                suspicious_events_analyzed,

            "ai_results":
                ai_results,

            "kpi_results":
                kpi_results,
        }

    finally:

        if df_rules is not None:

            try:
                df_rules.unpersist()
            except Exception:
                pass

        if df_prepared is not None:

            try:
                df_prepared.unpersist()
            except Exception:
                pass


# ============================================================
# ANALYSER UN DATASET IMPORTE
# ============================================================

def analyze_uploaded_dataset(
    upload_dir: Path,
    upload_id: str,
    persist_results: bool = True,
) -> Dict:
    """
    Lance automatiquement le pipeline approprié.

    Volume standard :
        Pandas.

    Gros volume :
        Apache Spark.

    Le moteur est choisi pendant la validation
    et réutilisé automatiquement ici.
    """

    # --------------------------------------------------------
    # 1. RETROUVER LE FICHIER
    # --------------------------------------------------------

    file_path = find_uploaded_file(
        upload_dir,
        upload_id,
    )

    # --------------------------------------------------------
    # 2. RECUPERER LE MOTEUR RECOMMANDE
    # --------------------------------------------------------

    engine = (
        _resolve_processing_engine(
            upload_dir,
            upload_id,
        )
    )

    # --------------------------------------------------------
    # 3. CREER LE RUN
    # --------------------------------------------------------

    if persist_results:

        analysis_run_id = create_analysis_run(
            upload_id=upload_id,
            filename=file_path.name,
        )

    else:

        analysis_run_id = (
            "dry-run-"
            f"{uuid4().hex}"
        )

    spark_session = None
    analysis_file_path = file_path
    sampling_info = {
        "applied": False,
        "source_rows": int(
            engine["row_count"] or 0
        ),
        "analyzed_rows": int(
            engine["row_count"] or 0
        ),
        "step": 1,
        "target_rows":
            PANDAS_WEB_SAMPLE_ROWS,
    }

    try:

        # ====================================================
        # 4. EXECUTER LE BON PIPELINE
        # ====================================================

        if (
            engine[
                "code"
            ]
            == "spark"
        ):

            spark_session = (
                create_spark_session(
                    app_name=
                        (
                            "PFA-Fleet-Platform-"
                            f"{analysis_run_id}"
                        )
                )
            )

            pipeline_results = (
                _run_spark_pipeline(
                    file_path,
                    spark_session,
                )
            )

        else:

            (
                analysis_file_path,
                sampling_info,
            ) = _prepare_pandas_analysis_file(
                file_path,
                engine["row_count"],
            )

            pipeline_results = (
                _run_pandas_pipeline(
                    analysis_file_path
                )
            )

        # ====================================================
        # 5. EXTRAIRE LES RESULTATS
        # ====================================================

        preparation_report = (
            pipeline_results[
                "preparation_report"
            ]
        )

        refueling_episodes = (
            pipeline_results[
                "refueling_episodes"
            ]
        )

        suspicious_events = (
            pipeline_results[
                "suspicious_events"
            ]
        )

        suspicious_events_analyzed = (
            pipeline_results[
                "suspicious_events_analyzed"
            ]
        )

        ai_results = (
            pipeline_results[
                "ai_results"
            ]
        )

        kpi_results = (
            pipeline_results[
                "kpi_results"
            ]
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

        # ====================================================
        # 6. TABLES PLATEFORME
        # ====================================================

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

        fact_fuel_alerts = (
            platform_results[
                "fact_fuel_alerts"
            ]
        )

        platform_summary = (
            platform_results[
                "summary"
            ]
        )

        controls = (
            platform_results[
                "controls"
            ]
        )

        # ====================================================
        # 7. POSTGRESQL
        # ====================================================

        if persist_results:

            database_result = (
                save_platform_results(
                    analysis_run_id=
                        analysis_run_id,

                    platform_results=
                        platform_results,
                )
            )

        else:

            database_result = {
                "database_saved":
                    False,

                "analysis_run_id":
                    analysis_run_id,

                "tables": {
                    table_name:
                        len(dataframe)

                    for (
                        table_name,
                        dataframe,
                    ) in platform_results.items()

                    if isinstance(
                        dataframe,
                        pd.DataFrame,
                    )
                },
            }

        # ====================================================
        # 8. CONFIANCE
        # ====================================================

        confiance_forte = _count_value(
            suspicious_events_analyzed,
            "confidence_level",
            "Forte",
        )

        confiance_moyenne = _count_value(
            suspicious_events_analyzed,
            "confidence_level",
            "Moyenne",
        )

        confiance_faible = _count_value(
            suspicious_events_analyzed,
            "confidence_level",
            "Faible",
        )

        # ====================================================
        # 9. PRIORITES
        # ====================================================

        priorite_p1 = _count_value(
            fact_fuel_alerts,
            "rang_priorite",
            1,
        )

        priorite_p2 = _count_value(
            fact_fuel_alerts,
            "rang_priorite",
            2,
        )

        priorite_p3 = _count_value(
            fact_fuel_alerts,
            "rang_priorite",
            3,
        )

        priorite_p4 = _count_value(
            fact_fuel_alerts,
            "rang_priorite",
            4,
        )

        priorite_p5 = _count_value(
            fact_fuel_alerts,
            "rang_priorite",
            5,
        )

        # ====================================================
        # 10. REPONSE FASTAPI
        # ====================================================

        return {
            "status":
                "completed",

            "upload_id":
                upload_id,

            "analysis_run_id":
                analysis_run_id,

            "filename":
                file_path.name,

            # ------------------------------------------------
            # MOTEUR
            # ------------------------------------------------

            "moteur_code":
                engine[
                    "code"
                ],

            "moteur_utilise":
                engine[
                    "label"
                ],

            "raison_moteur":
                engine[
                    "reason"
                ],

            "nombre_lignes_validation":
                engine[
                    "row_count"
                ],

            "seuil_spark_lignes":
                engine[
                    "spark_threshold"
                ],

            "web_sampling":
                sampling_info,

            # ------------------------------------------------
            # PREPARATION
            # ------------------------------------------------

            "preparation": {

                "nombre_lignes_brutes":
                    int(
                        preparation_report[
                            "nombre_lignes_brutes"
                        ]
                    ),

                "nombre_lignes_source":
                    int(
                        sampling_info[
                            "source_rows"
                        ]
                    ),

                "echantillonnage_applique":
                    bool(
                        sampling_info[
                            "applied"
                        ]
                    ),

                "nombre_lignes_preparees":
                    int(
                        preparation_report[
                            "nombre_lignes_preparees"
                        ]
                    ),

                "nombre_vehicules":
                    int(
                        preparation_report[
                            "nombre_vehicules"
                        ]
                    ),

                "nombre_fuel_hors_plage":
                    int(
                        preparation_report[
                            "nombre_fuel_hors_plage"
                        ]
                    ),
            },

            # ------------------------------------------------
            # REGLES
            # ------------------------------------------------

            "rules": {

                "nombre_ravitaillements":
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
            },

            # ------------------------------------------------
            # CONTEXTE
            # ------------------------------------------------

            "context": {

                "nombre_evenements_analyses":
                    int(
                        len(
                            suspicious_events_analyzed
                        )
                    ),

                "confiance_forte":
                    confiance_forte,

                "confiance_moyenne":
                    confiance_moyenne,

                "confiance_faible":
                    confiance_faible,
            },

            # ------------------------------------------------
            # IA
            # ------------------------------------------------

            "ai": {

                "nombre_baisses_analysees":
                    int(
                        ai_results[
                            "summary"
                        ][
                            "nombre_baisses_analysees"
                        ]
                    ),

                "nombre_candidats_ia":
                    int(
                        ai_results[
                            "summary"
                        ][
                            "nombre_candidats_ia"
                        ]
                    ),

                "nombre_regle_et_ia":
                    int(
                        ai_results[
                            "summary"
                        ][
                            "nombre_overlap_regles_ia"
                        ]
                    ),

                "taux_recouvrement_pct":
                    float(
                        ai_results[
                            "summary"
                        ][
                            "taux_recouvrement_pct"
                        ]
                    ),
            },

            # ------------------------------------------------
            # KPI
            # ------------------------------------------------

            "kpi": {

                "nombre_vehicules":
                    int(
                        kpi_global[
                            "nombre_vehicules"
                        ]
                    ),

                "nombre_total_mesures":
                    int(
                        kpi_global[
                            "nombre_total_mesures"
                        ]
                    ),

                "distance_totale_km":
                    float(
                        kpi_global[
                            "distance_totale_km"
                        ]
                    ),
            },

            # ------------------------------------------------
            # PLATEFORME
            # ------------------------------------------------

            "platform": {

                **platform_summary,

                "priorites": {

                    "P1":
                        priorite_p1,

                    "P2":
                        priorite_p2,

                    "P3":
                        priorite_p3,

                    "P4":
                        priorite_p4,

                    "P5":
                        priorite_p5,
                },
            },

            # ------------------------------------------------
            # POSTGRESQL
            # ------------------------------------------------

            "database": {

                "saved":
                    database_result[
                        "database_saved"
                    ],

                "analysis_run_id":
                    analysis_run_id,

                "tables":
                    database_result[
                        "tables"
                    ],
            },

            # ------------------------------------------------
            # CONTROLES
            # ------------------------------------------------

            "quality_controls":
                controls,
        }

    # ========================================================
    # ERREUR
    # ========================================================

    except Exception as error:

        if persist_results:

            try:

                mark_analysis_run_failed(
                    analysis_run_id=
                        analysis_run_id,

                    error_message=
                        str(error),
                )

            except Exception:
                pass

        raise

    # ========================================================
    # ARRET DE SPARK
    # ========================================================

    finally:

        if spark_session is not None:

            try:

                spark_session.stop()

            except Exception:
                pass

        if analysis_file_path != file_path:

            try:

                analysis_file_path.unlink(
                    missing_ok=True
                )

            except OSError:
                pass
