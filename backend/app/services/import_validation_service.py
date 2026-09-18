import json
import os
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import pyarrow.parquet as pq


# ============================================================
# COLONNES DU PIPELINE
# ============================================================

# Colonnes absolument nécessaires
# au pipeline complet actuel.
REQUIRED_COLUMNS = [
    "deviceId",
    "fixTime",
    "latitude",
    "longitude",
    "speed",
    "fuelLevel",
    "odometer",
    "ignition",
]


# Colonnes utilisées pour décrire
# le contexte disponible dans l'interface.
CONTEXT_COLUMNS = [
    "speed",
    "odometer",
    "latitude",
    "longitude",
    "ignition",
]


# ============================================================
# PARAMETRES DE VALIDATION
# ============================================================

# Taille des blocs lus dans les gros fichiers.
CHUNK_SIZE = 100_000


# Seuil de routage vers Spark.
#
# Il peut être modifié sans changer le code :
#
# $env:PFA_SPARK_ROW_THRESHOLD="2000000"
#
SPARK_ROW_THRESHOLD = int(
    os.getenv(
        "PFA_SPARK_ROW_THRESHOLD",
        "1000000",
    )
)


# ============================================================
# FICHIER DE METADONNEES DE VALIDATION
# ============================================================

def get_validation_metadata_path(
    upload_dir: Path,
    upload_id: str,
) -> Path:
    """
    Chemin du petit fichier JSON qui mémorise
    le résultat utile de la validation.
    """

    return (
        upload_dir
        / f"{upload_id}.validation.json"
    )


def save_validation_metadata(
    upload_dir: Path,
    upload_id: str,
    validation_result: Dict,
) -> None:
    """
    Mémorise les informations nécessaires
    pour l'étape d'analyse.

    Cela évite de recompter toutes les lignes
    lorsque l'utilisateur clique ensuite
    sur "Lancer l'analyse".
    """

    metadata = {
        "upload_id":
            upload_id,

        "nombre_lignes":
            validation_result[
                "nombre_lignes"
            ],

        "nombre_vehicules":
            validation_result[
                "nombre_vehicules"
            ],

        "compatible":
            validation_result[
                "compatible"
            ],

        "moteur_recommande":
            validation_result[
                "moteur_recommande"
            ],

        "moteur_libelle":
            validation_result[
                "moteur_libelle"
            ],

        "seuil_spark_lignes":
            validation_result[
                "seuil_spark_lignes"
            ],

        "raison_moteur":
            validation_result[
                "raison_moteur"
            ],
    }

    metadata_path = (
        get_validation_metadata_path(
            upload_dir,
            upload_id,
        )
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_validation_metadata(
    upload_dir: Path,
    upload_id: str,
) -> Optional[Dict]:
    """
    Relit les métadonnées mémorisées
    après la validation.
    """

    metadata_path = (
        get_validation_metadata_path(
            upload_dir,
            upload_id,
        )
    )

    if not metadata_path.exists():
        return None

    return json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )


# ============================================================
# SELECTION DU MOTEUR
# ============================================================

def select_processing_engine(
    row_count: int,
) -> Dict:
    """
    Sélectionne automatiquement le moteur
    selon le volume du dataset.
    """

    if row_count >= SPARK_ROW_THRESHOLD:

        return {
            "moteur_recommande":
                "spark",

            "moteur_libelle":
                "Apache Spark",

            "seuil_spark_lignes":
                SPARK_ROW_THRESHOLD,

            "raison_moteur":
                (
                    "Volume important : "
                    "Apache Spark est recommandé "
                    "pour la montée en charge."
                ),
        }

    return {
        "moteur_recommande":
            "pandas",

        "moteur_libelle":
            "Pandas",

        "seuil_spark_lignes":
            SPARK_ROW_THRESHOLD,

        "raison_moteur":
            (
                "Volume standard : "
                "Pandas est adapté au traitement."
            ),
    }


# ============================================================
# TROUVER LE FICHIER
# ============================================================

def find_uploaded_file(
    upload_dir: Path,
    upload_id: str,
) -> Optional[Path]:
    """
    Recherche le fichier correspondant
    à l'identifiant d'import.
    """

    for extension in [
        ".csv",
        ".parquet",
    ]:

        file_path = (
            upload_dir
            / f"{upload_id}{extension}"
        )

        if file_path.exists():
            return file_path

    return None


# ============================================================
# STATISTIQUES
# ============================================================

def update_statistics(
    chunk: pd.DataFrame,
    vehicle_ids: set,
    missing_counts: Dict[str, int],
    start_date,
    end_date,
):
    """
    Met à jour les statistiques
    pendant la lecture du dataset.
    """

    # --------------------------------------------------------
    # Valeurs manquantes
    # --------------------------------------------------------

    for column in missing_counts:

        if column in chunk.columns:

            missing_counts[
                column
            ] += int(
                chunk[
                    column
                ].isna().sum()
            )

    # --------------------------------------------------------
    # Véhicules distincts
    # --------------------------------------------------------

    if "deviceId" in chunk.columns:

        values = (
            chunk[
                "deviceId"
            ]
            .dropna()
            .astype(str)
            .unique()
        )

        vehicle_ids.update(
            values
        )

    # --------------------------------------------------------
    # Période temporelle
    # --------------------------------------------------------

    if "fixTime" in chunk.columns:

        dates = (
            pd.to_datetime(
                chunk[
                    "fixTime"
                ],
                errors="coerce",
                utc=True,
            )
            .dropna()
        )

        if not dates.empty:

            chunk_start = (
                dates.min()
            )

            chunk_end = (
                dates.max()
            )

            if (
                start_date is None
                or
                chunk_start < start_date
            ):
                start_date = (
                    chunk_start
                )

            if (
                end_date is None
                or
                chunk_end > end_date
            ):
                end_date = (
                    chunk_end
                )

    return (
        start_date,
        end_date,
    )


# ============================================================
# VALIDATION CSV
# ============================================================

def validate_csv(
    file_path: Path,
):
    """
    Validation d'un fichier CSV.

    Le fichier est lu par blocs afin
    de ne pas charger tout le dataset
    en mémoire.
    """

    # --------------------------------------------------------
    # En-tête uniquement
    # --------------------------------------------------------

    header = pd.read_csv(
        file_path,
        sep=None,
        engine="python",
        nrows=0,
    )

    columns = (
        list(
            header.columns
        )
    )

    useful_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column in columns
    ]

    missing_counts = {
        column: 0
        for column in useful_columns
    }

    vehicle_ids = set()

    row_count = 0

    start_date = None
    end_date = None

    # --------------------------------------------------------
    # Lecture par blocs
    # --------------------------------------------------------

    for chunk in pd.read_csv(
        file_path,
        sep=None,
        engine="python",
        chunksize=CHUNK_SIZE,
    ):

        row_count += (
            len(chunk)
        )

        (
            start_date,
            end_date,
        ) = update_statistics(
            chunk,
            vehicle_ids,
            missing_counts,
            start_date,
            end_date,
        )

    return {
        "columns":
            columns,

        "row_count":
            row_count,

        "vehicle_ids":
            vehicle_ids,

        "missing_counts":
            missing_counts,

        "start_date":
            start_date,

        "end_date":
            end_date,
    }


# ============================================================
# VALIDATION PARQUET
# ============================================================

def validate_parquet(
    file_path: Path,
):
    """
    Validation d'un fichier Parquet.
    """

    parquet_file = (
        pq.ParquetFile(
            file_path
        )
    )

    columns = (
        parquet_file.schema.names
    )

    row_count = (
        parquet_file
        .metadata
        .num_rows
    )

    useful_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column in columns
    ]

    missing_counts = {
        column: 0
        for column in useful_columns
    }

    vehicle_ids = set()

    start_date = None
    end_date = None

    # --------------------------------------------------------
    # Lecture des colonnes utiles uniquement
    # --------------------------------------------------------

    if useful_columns:

        for batch in (
            parquet_file
            .iter_batches(
                batch_size=
                    CHUNK_SIZE,

                columns=
                    useful_columns,
            )
        ):

            chunk = (
                batch.to_pandas()
            )

            (
                start_date,
                end_date,
            ) = update_statistics(
                chunk,
                vehicle_ids,
                missing_counts,
                start_date,
                end_date,
            )

    return {
        "columns":
            columns,

        "row_count":
            int(
                row_count
            ),

        "vehicle_ids":
            vehicle_ids,

        "missing_counts":
            missing_counts,

        "start_date":
            start_date,

        "end_date":
            end_date,
    }


# ============================================================
# VALIDATION PRINCIPALE
# ============================================================

def validate_dataset(
    upload_dir: Path,
    upload_id: str,
):
    """
    Fonction principale de validation.

    Elle :
    1. valide le fichier ;
    2. compte les lignes ;
    3. vérifie les colonnes ;
    4. détermine le moteur recommandé ;
    5. mémorise ce choix pour l'analyse.
    """

    # --------------------------------------------------------
    # Fichier
    # --------------------------------------------------------

    file_path = (
        find_uploaded_file(
            upload_dir,
            upload_id,
        )
    )

    if file_path is None:

        raise FileNotFoundError(
            "Fichier importé introuvable."
        )

    extension = (
        file_path.suffix.lower()
    )

    # --------------------------------------------------------
    # Validation selon format
    # --------------------------------------------------------

    if extension == ".csv":

        result = (
            validate_csv(
                file_path
            )
        )

    elif extension == ".parquet":

        result = (
            validate_parquet(
                file_path
            )
        )

    else:

        raise ValueError(
            "Format de fichier non supporté."
        )

    columns = (
        result[
            "columns"
        ]
    )

    row_count = int(
        result[
            "row_count"
        ]
    )

    # --------------------------------------------------------
    # Colonnes obligatoires
    # --------------------------------------------------------

    missing_required = [
        column
        for column in REQUIRED_COLUMNS
        if column not in columns
    ]

    # --------------------------------------------------------
    # Colonnes de contexte
    # --------------------------------------------------------

    context_present = [
        column
        for column in CONTEXT_COLUMNS
        if column in columns
    ]

    missing_context = [
        column
        for column in CONTEXT_COLUMNS
        if column not in columns
    ]

    # --------------------------------------------------------
    # Pourcentage de valeurs manquantes
    # --------------------------------------------------------

    missing_percentages = {}

    for (
        column,
        missing_count,
    ) in result[
        "missing_counts"
    ].items():

        if row_count > 0:

            percentage = (
                missing_count
                /
                row_count
                *
                100
            )

        else:

            percentage = 0

        missing_percentages[
            column
        ] = round(
            percentage,
            2,
        )

    # --------------------------------------------------------
    # Compatibilité
    # --------------------------------------------------------

    if row_count == 0:

        compatible = False

        analysis_level = (
            "Incompatible"
        )

        message = (
            "Le dataset ne contient "
            "aucune ligne exploitable."
        )

    elif missing_required:

        compatible = False

        analysis_level = (
            "Incompatible"
        )

        message = (
            "Le dataset ne contient pas toutes "
            "les colonnes nécessaires au "
            "pipeline complet."
        )

    else:

        compatible = True

        analysis_level = (
            "Analyse complète"
        )

        message = (
            "Le dataset contient toutes les "
            "colonnes nécessaires à "
            "l'analyse complète."
        )

    # --------------------------------------------------------
    # Sélection du moteur
    # --------------------------------------------------------

    if compatible:

        engine_result = (
            select_processing_engine(
                row_count
            )
        )

    else:

        engine_result = {
            "moteur_recommande":
                None,

            "moteur_libelle":
                None,

            "seuil_spark_lignes":
                SPARK_ROW_THRESHOLD,

            "raison_moteur":
                (
                    "Aucun moteur sélectionné : "
                    "le dataset doit d'abord "
                    "être compatible."
                ),
        }

    # --------------------------------------------------------
    # Période
    # --------------------------------------------------------

    start_date = (
        result[
            "start_date"
        ]
    )

    end_date = (
        result[
            "end_date"
        ]
    )

    # --------------------------------------------------------
    # Réponse finale
    # --------------------------------------------------------

    validation_result = {
        "upload_id":
            upload_id,

        "extension":
            extension,

        "nombre_lignes":
            row_count,

        "nombre_colonnes":
            len(columns),

        "nombre_vehicules":
            (
                len(
                    result[
                        "vehicle_ids"
                    ]
                )
                if "deviceId" in columns
                else None
            ),

        "debut_periode":
            (
                start_date.isoformat()
                if start_date is not None
                else None
            ),

        "fin_periode":
            (
                end_date.isoformat()
                if end_date is not None
                else None
            ),

        "colonnes_detectees":
            columns,

        "colonnes_requises":
            REQUIRED_COLUMNS,

        "colonnes_requises_manquantes":
            missing_required,

        "colonnes_contexte_presentes":
            context_present,

        "colonnes_contexte_manquantes":
            missing_context,

        "valeurs_manquantes_pct":
            missing_percentages,

        "compatible":
            compatible,

        "niveau_analyse":
            analysis_level,

        "message":
            message,

        "moteur_recommande":
            engine_result[
                "moteur_recommande"
            ],

        "moteur_libelle":
            engine_result[
                "moteur_libelle"
            ],

        "seuil_spark_lignes":
            engine_result[
                "seuil_spark_lignes"
            ],

        "raison_moteur":
            engine_result[
                "raison_moteur"
            ],
    }

    # --------------------------------------------------------
    # Mémorisation pour /analyze
    # --------------------------------------------------------

    save_validation_metadata(
        upload_dir,
        upload_id,
        validation_result,
    )

    return validation_result