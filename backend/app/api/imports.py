from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.schemas.imports import (
    DatasetValidationResponse,
)

from app.services.import_validation_service import (
    validate_dataset,
)

from app.services.import_analysis_service import (
    analyze_uploaded_dataset,
)


router = APIRouter(
    prefix="/api/imports",
    tags=["Imports"],
)


# Racine du projet pfa-fleet-platform
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Dossier où les fichiers importés sont stockés
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# Formats autorisés
ALLOWED_EXTENSIONS = {
    ".csv",
    ".parquet",
}


# =========================================================
# 1. UPLOAD D'UN FICHIER
# =========================================================

@router.post("/upload")
async def upload_fleet_file(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Nom de fichier manquant.",
        )

    # Sécuriser le nom original
    original_filename = Path(
        file.filename
    ).name

    extension = Path(
        original_filename
    ).suffix.lower()

    # Vérifier le format
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Format non supporté. "
                "Utilisez un fichier CSV ou Parquet."
            ),
        )

    # Identifiant unique de l'import
    upload_id = uuid4().hex

    stored_filename = (
        f"{upload_id}{extension}"
    )

    destination = (
        UPLOAD_DIR / stored_filename
    )

    size_bytes = 0

    try:

        # Lecture par blocs de 1 MB
        with destination.open("wb") as output_file:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                output_file.write(
                    chunk
                )

                size_bytes += len(
                    chunk
                )

    except Exception:

        # Supprimer le fichier incomplet
        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur pendant "
                "l'enregistrement du fichier."
            ),
        )

    finally:

        await file.close()

    return {
        "status": "uploaded",
        "upload_id": upload_id,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "extension": extension,
        "size_bytes": size_bytes,
    }


# =========================================================
# 2. VALIDATION DU DATASET
# =========================================================

@router.post(
    "/{upload_id}/validate",
    response_model=DatasetValidationResponse,
)
def validate_uploaded_dataset(
    upload_id: str,
):
    try:

        result = validate_dataset(
            UPLOAD_DIR,
            upload_id,
        )

        return result

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "Erreur validation dataset:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur pendant la validation "
                "du dataset."
            ),
        )


# =========================================================
# 3. ANALYSE DU DATASET
# =========================================================

@router.post(
    "/{upload_id}/analyze"
)
def analyze_uploaded_file(
    upload_id: str,
):
    """
    Lance le pipeline complet sur un fichier
    déjà importé dans la plateforme.

    Pipeline :
    préparation
    -> règles
    -> analyse contextuelle
    -> Isolation Forest
    -> KPI
    -> tables plateforme
    """

    try:

        result = analyze_uploaded_dataset(
            UPLOAD_DIR,
            upload_id,
        )

        return result

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "Erreur analyse dataset:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur pendant l'analyse "
                "du dataset."
            ),
        )