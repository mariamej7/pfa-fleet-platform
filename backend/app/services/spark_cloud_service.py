import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional

from sqlalchemy import text

from app.core.database import engine


GITHUB_API_VERSION = "2022-11-28"
DEFAULT_REPOSITORY = "mariamej7/pfa-fleet-platform"
DEFAULT_WORKFLOW = "spark-analysis.yml"
DEFAULT_BACKEND_URL = (
    "https://pfa-fleet-platform.onrender.com"
)


def spark_cloud_is_configured() -> bool:
    return bool(
        os.getenv(
            "GITHUB_SPARK_TOKEN",
            "",
        ).strip()
    )


def dispatch_spark_analysis(
    upload_id: str,
    analysis_run_id: str,
    extension: str,
) -> dict:
    """Déclenche le workflow Spark sans exposer le jeton au navigateur."""

    token = os.getenv(
        "GITHUB_SPARK_TOKEN",
        "",
    ).strip()

    if not token:
        raise RuntimeError(
            "Le moteur Spark cloud n'est pas configuré."
        )

    repository = os.getenv(
        "GITHUB_SPARK_REPOSITORY",
        DEFAULT_REPOSITORY,
    ).strip()

    workflow = os.getenv(
        "GITHUB_SPARK_WORKFLOW",
        DEFAULT_WORKFLOW,
    ).strip()

    workflow_ref = os.getenv(
        "GITHUB_SPARK_REF",
        "main",
    ).strip()

    backend_url = (
        os.getenv(
            "SPARK_BACKEND_URL",
            "",
        ).strip()
        or os.getenv(
            "RENDER_EXTERNAL_URL",
            "",
        ).strip()
        or DEFAULT_BACKEND_URL
    ).rstrip("/")

    payload = json.dumps(
        {
            "ref": workflow_ref,
            "inputs": {
                "upload_id": upload_id,
                "analysis_run_id": analysis_run_id,
                "file_extension": extension.lstrip("."),
                "backend_url": backend_url,
            },
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        (
            "https://api.github.com/repos/"
            f"{repository}/actions/workflows/"
            f"{workflow}/dispatches"
        ),
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Content-Type": "application/json",
            "User-Agent": "pfa-fleet-platform",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=20,
        ) as response:
            status_code = response.status

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            (
                "GitHub n'a pas accepté le lancement "
                f"du traitement Spark (HTTP {error.code})."
            )
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            "GitHub est temporairement inaccessible."
        ) from error

    if status_code != 204:
        raise RuntimeError(
            "Réponse inattendue du service Spark cloud."
        )

    return {
        "status": "queued",
        "execution_mode": "spark_cloud",
        "analysis_run_id": analysis_run_id,
        "upload_id": upload_id,
        "message": (
            "Le traitement Apache Spark a été lancé. "
            "Cette analyse peut prendre plusieurs minutes."
        ),
    }


def get_analysis_run_status(
    upload_id: str,
    analysis_run_id: Optional[str] = None,
) -> Optional[dict]:
    parameters = {
        "upload_id": upload_id,
    }

    if analysis_run_id:
        query = text(
            """
            SELECT
                analysis_run_id,
                upload_id,
                filename,
                status,
                created_at,
                completed_at,
                nombre_lignes_preparees,
                nombre_vehicules,
                nombre_alertes_finales,
                error_message
            FROM analysis_runs
            WHERE
                upload_id = :upload_id
                AND analysis_run_id = :analysis_run_id
            LIMIT 1
            """
        )
        parameters[
            "analysis_run_id"
        ] = analysis_run_id
    else:
        query = text(
            """
            SELECT
                analysis_run_id,
                upload_id,
                filename,
                status,
                created_at,
                completed_at,
                nombre_lignes_preparees,
                nombre_vehicules,
                nombre_alertes_finales,
                error_message
            FROM analysis_runs
            WHERE upload_id = :upload_id
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

    with engine.connect() as connection:
        row = (
            connection.execute(
                query,
                parameters,
            )
            .mappings()
            .first()
        )

    if row is None:
        return None

    result = dict(row)

    for field_name in (
        "created_at",
        "completed_at",
    ):
        value = result.get(
            field_name
        )

        if isinstance(value, datetime):
            result[field_name] = (
                value.isoformat()
            )

    return result
