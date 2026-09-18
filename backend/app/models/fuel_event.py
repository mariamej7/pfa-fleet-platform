from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FuelEvent(Base):
    __tablename__ = "fact_fuel_events"

    # Identifiant unique de l'événement
    event_id: Mapped[str] = mapped_column(
        Text,
        primary_key=True,
    )

    # Véhicule concerné
    deviceId: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Date et heure de l'événement
    event_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Type d'événement
    event_category: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Source de détection
    source_detection: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Priorité d'investigation
    priorite_alerte: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Variation du niveau de carburant
    variation_fuel_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Niveau de carburant au moment de l'événement
    fuel_level_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Niveau de confiance de l'analyse contextuelle
    confidence_level: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Score de l'Isolation Forest
    ai_score_percentile: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Position GPS
    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Lien permettant d'ouvrir la position sur une carte
    lien_carte: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )