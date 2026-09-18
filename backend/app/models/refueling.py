from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RefuelingEvent(Base):
    __tablename__ = "fact_refueling_events"

    # Identifiant unique de l'événement
    event_id: Mapped[str] = mapped_column(
        Text,
        primary_key=True,
    )

    # Identifiant de l'épisode de ravitaillement
    refuel_episode_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Véhicule concerné
    deviceId: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Début et fin de l'épisode
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Durée de l'épisode
    duration_sec: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Nombre de variations regroupées
    n_steps: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Niveau de carburant
    start_fuel_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    end_fuel_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    total_delta_fuel_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Vitesse pendant l'épisode
    max_speed_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    mean_speed_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Informations génériques d'événement
    event_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    event_category: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    source_detection: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    variation_fuel_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    fuel_level_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )