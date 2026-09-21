
import hashlib
import hmac
import os
import re
import secrets
import time
from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse

from app.schemas.imports import (
    DatasetValidationResponse,
)

from app.services.import_validation_service import (
    find_uploaded_file,
    load_validation_metadata,
    validate_dataset,
)

from app.services.import_analysis_service import (
    analyze_uploaded_dataset,
)

from app.services.database_persistence_service import (
    create_analysis_run,
    mark_analysis_run_failed,
)

from app.services.spark_cloud_service import (
    dispatch_spark_analysis,
    get_analysis_run_status,
    spark_cloud_is_configured,
)


IMPORT_TOKEN_TTL_SECONDS = max(
    60,
    min(
        int(
            os.getenv(
                "IMPORT_TOKEN_TTL_SECONDS",
                "900",
            )
        ),
        900,
    ),
)


def _is_valid_import_token(
    token: str | None,
    secret_key: str,
) -> bool:
    if not token:
        return False

    try:
        issued_at_raw, nonce, signature = (
            token.split(".", 2)
        )

        if not re.fullmatch(
            r"[0-9]{10,}",
            issued_at_raw,
        ):
            return False

        if not re.fullmatch(
            r"[0-9a-fA-F]{32}",
            nonce,
        ):
            return False

        if not re.fullmatch(
            r"[0-9a-fA-F]{64}",
            signature,
        ):
            return False

        issued_at = int(
            issued_at_raw
        )
        now = int(time.time())

        if issued_at > now + 30:
            return False

        if (
            now - issued_at
            > IMPORT_TOKEN_TTL_SECONDS
        ):
            return False

        payload = (
            f"{issued_at_raw}.{nonce}"
            .encode("utf-8")
        )

        expected_signature = hmac.new(
            secret_key.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return secrets.compare_digest(
            signature,
            expected_signature,
        )

    except (TypeError, ValueError):
        return False


def require_import_key(
    x_import_key: str | None = Header(default=None),
    x_import_token: str | None = Header(default=None),
) -> None:
    expected_key = os.getenv(
        "IMPORT_API_KEY",
        "",
    ).strip()

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "La clé d'import n'est pas configurée "
                "sur le serveur."
            ),
        )

    key_is_valid = bool(
        x_import_key
        and secrets.compare_digest(
            x_import_key,
            expected_key,
        )
    )

    token_is_valid = _is_valid_import_token(
        x_import_token,
        expected_key,
    )

    if not key_is_valid and not token_is_valid:
        raise HTTPException(
            status_code=401,
            detail="Autorisation d'import invalide.",
        )


router = APIRouter(
    prefix="/api/imports",
    tags=["Imports"],
    dependencies=[Depends(require_import_key)],
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

# Le transfert est écrit sur disque par blocs. Le calcul Spark est délégué
# au runner cloud afin de ne pas charger le fichier complet dans Render.
MAX_UPLOAD_SIZE_MB = max(
    1,
    int(
        os.getenv(
            "IMPORT_MAX_UPLOAD_SIZE_MB",
            "100",
        )
    ),
)

MAX_UPLOAD_SIZE_BYTES = (
    MAX_UPLOAD_SIZE_MB
    * 1024
    * 1024
)

_analysis_lock = Lock()


def _is_valid_upload_id(
    upload_id: str,
) -> bool:
    return bool(
        re.fullmatch(
            r"[0-9a-fA-F]{32}",
            upload_id,
        )
    )


def _require_valid_upload_id(
    upload_id: str,
) -> None:
    if not _is_valid_upload_id(
        upload_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Identifiant d'import invalide."
            ),
        )


def _cleanup_upload_files(
    upload_id: str,
) -> None:
    """Supprime les fichiers temporaires liés à un import."""

    if not _is_valid_upload_id(
        upload_id
    ):
        return

    for suffix in (
        ".csv",
        ".parquet",
        ".validation.json",
    ):
        file_path = (
            UPLOAD_DIR
            / f"{upload_id}{suffix}"
        )

        try:
            file_path.unlink(
                missing_ok=True
            )
        except OSError:
            # Le stockage Render est temporaire.
            # Une suppression impossible ne doit pas masquer
            # le résultat de l'analyse.
            pass


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

        # Lecture par blocs de 1 Mo
        with destination.open("wb") as output_file:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                # Refuser un fichier dépassant la limite de démonstration
                if (
                    size_bytes + len(chunk)
                    > MAX_UPLOAD_SIZE_BYTES
                ):
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "Fichier trop volumineux. "
                            f"Taille maximale : {MAX_UPLOAD_SIZE_MB} Mo."
                        ),
                    )

                output_file.write(
                    chunk
                )

                size_bytes += len(
                    chunk
                )

    except HTTPException:

        # Supprimer le fichier incomplet
        # et conserver le code HTTP 413
        if destination.exists():
            destination.unlink()

        raise

    except Exception:

        # Supprimer le fichier incomplet
        # si une autre erreur survient
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

    if size_bytes == 0:
        destination.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=400,
            detail="Le fichier est vide.",
        )

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
    _require_valid_upload_id(
        upload_id
    )

    try:

        result = validate_dataset(
            UPLOAD_DIR,
            upload_id,
        )

        if not result.get(
            "compatible",
            False,
        ):
            _cleanup_upload_files(
                upload_id
            )

        return result

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except ValueError as error:

        _cleanup_upload_files(
            upload_id
        )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        _cleanup_upload_files(
            upload_id
        )

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
# 3. TRANSFERT ET SUIVI DU TRAITEMENT SPARK CLOUD
# =========================================================

@router.get(
    "/{upload_id}/download"
)
def download_uploaded_dataset(
    upload_id: str,
):
    """Téléchargement protégé utilisé uniquement par GitHub Actions."""

    _require_valid_upload_id(
        upload_id
    )

    file_path = find_uploaded_file(
        UPLOAD_DIR,
        upload_id,
    )

    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail="Fichier importé introuvable.",
        )

    media_type = (
        "text/csv"
        if file_path.suffix.lower() == ".csv"
        else "application/octet-stream"
    )

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type=media_type,
    )


@router.post(
    "/{upload_id}/status"
)
def get_uploaded_analysis_status(
    upload_id: str,
    analysis_run_id: str | None = Query(
        default=None,
    ),
):
    _require_valid_upload_id(
        upload_id
    )

    result = get_analysis_run_status(
        upload_id,
        analysis_run_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Analyse introuvable.",
        )

    return result


@router.post(
    "/{upload_id}/cleanup"
)
def cleanup_cloud_upload(
    upload_id: str,
):
    _require_valid_upload_id(
        upload_id
    )

    _cleanup_upload_files(
        upload_id
    )

    return {
        "status": "cleaned",
        "upload_id": upload_id,
    }


@router.post(
    "/{upload_id}/spark-failed"
)
def mark_cloud_analysis_failed(
    upload_id: str,
    analysis_run_id: str = Query(...),
):
    _require_valid_upload_id(
        upload_id
    )

    run = get_analysis_run_status(
        upload_id,
        analysis_run_id,
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Analyse introuvable.",
        )

    mark_analysis_run_failed(
        analysis_run_id,
        (
            "Le traitement Spark cloud a échoué. "
            "Consultez les journaux GitHub Actions."
        ),
    )

    _cleanup_upload_files(
        upload_id
    )

    return {
        "status": "failed",
        "analysis_run_id": analysis_run_id,
    }


# =========================================================
# 4. ANALYSE DU DATASET
# =========================================================

@router.post(
    "/{upload_id}/analyze"
)
def analyze_uploaded_file(
    upload_id: str,
    persist: bool = Query(
        default=True,
        description=(
            "Enregistrer les résultats dans PostgreSQL. "
            "Utiliser false pour un test sans remplacer "
            "le dataset actif."
        ),
    ),
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

    _require_valid_upload_id(
        upload_id
    )

    if not _analysis_lock.acquire(
        blocking=False
    ):
        raise HTTPException(
            status_code=429,
            detail=(
                "Une analyse est déjà en cours. "
                "Réessayez dans quelques instants."
            ),
            headers={
                "Retry-After": "30",
            },
        )

    cleanup_after_request = True

    try:

        metadata = load_validation_metadata(
            UPLOAD_DIR,
            upload_id,
        )

        if metadata is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Le fichier doit être validé "
                    "avant de lancer l'analyse."
                ),
            )

        if (
            metadata.get(
                "moteur_recommande"
            )
            == "spark"
        ):
            if not persist:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Le test sans enregistrement n'est pas "
                        "disponible pour Spark cloud."
                    ),
                )

            if not spark_cloud_is_configured():
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Le moteur Spark cloud n'est pas encore "
                        "configuré sur le serveur."
                    ),
                )

            file_path = find_uploaded_file(
                UPLOAD_DIR,
                upload_id,
            )

            if file_path is None:
                raise FileNotFoundError(
                    "Fichier importé introuvable."
                )

            analysis_run_id = create_analysis_run(
                upload_id=upload_id,
                filename=file_path.name,
            )

            try:
                result = dispatch_spark_analysis(
                    upload_id=upload_id,
                    analysis_run_id=
                        analysis_run_id,
                    extension=file_path.suffix,
                )

            except RuntimeError as error:
                mark_analysis_run_failed(
                    analysis_run_id,
                    str(error),
                )

                raise HTTPException(
                    status_code=503,
                    detail=str(error),
                ) from error

            cleanup_after_request = False

            return result

        result = analyze_uploaded_dataset(
            UPLOAD_DIR,
            upload_id,
            persist_results=persist,
        )

        return result

    except HTTPException:

        raise

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

    finally:

        if cleanup_after_request:
            _cleanup_upload_files(
                upload_id
            )

        _analysis_lock.release()
