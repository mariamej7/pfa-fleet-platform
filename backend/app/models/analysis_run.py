from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    # Identifiant unique d'une exécution du pipeline
    analysis_run_id: Mapped[str] = mapped_column(
        Text,
        primary_key=True,
    )

    # Identifiant du fichier importé
    upload_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Nom du fichier analysé
    filename: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # uploaded / processing / completed / failed
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Date de début de l'analyse
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    # Date de fin de l'analyse
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Indique quelle analyse alimente actuellement le dashboard
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Quelques informations utiles sur le run
    nombre_lignes_preparees: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    nombre_vehicules: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    nombre_alertes_finales: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Message enregistré seulement si l'analyse échoue
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )