import argparse
from pathlib import Path

from app.services.import_analysis_service import (
    analyze_uploaded_dataset,
)
from app.services.import_validation_service import (
    validate_dataset,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Exécute une analyse Spark cloud "
            "pour un fichier déjà téléchargé."
        )
    )
    parser.add_argument(
        "--upload-dir",
        required=True,
    )
    parser.add_argument(
        "--upload-id",
        required=True,
    )
    parser.add_argument(
        "--analysis-run-id",
        required=True,
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    upload_dir = Path(
        arguments.upload_dir
    ).resolve()

    validation = validate_dataset(
        upload_dir,
        arguments.upload_id,
    )

    if not validation.get(
        "compatible",
        False,
    ):
        raise ValueError(
            validation.get(
                "message",
                "Le fichier n'est pas compatible.",
            )
        )

    if (
        validation.get(
            "moteur_recommande"
        )
        != "spark"
    ):
        raise ValueError(
            "Le fichier n'a pas été routé vers Apache Spark."
        )

    result = analyze_uploaded_dataset(
        upload_dir,
        arguments.upload_id,
        persist_results=True,
        analysis_run_id=
            arguments.analysis_run_id,
    )

    print(
        (
            "Analyse Spark terminée : "
            f"{result['analysis_run_id']}"
        )
    )


if __name__ == "__main__":
    main()
