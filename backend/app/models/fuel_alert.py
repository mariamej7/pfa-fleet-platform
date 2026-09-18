from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FuelAlert(Base):
    __tablename__ = "fact_fuel_alerts"

    # Identifiant unique de l'alerte
    alert_id: Mapped[str] = mapped_column(
        Text,
        primary_key=True,
    )

    # Véhicule
    deviceId: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Date et heure de l'événement
    fixTime: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Informations de détection
    alert_type: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    source_detection: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    suspicious_event_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Carburant
    fuelLevel: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    drop_abs_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Temps et mouvement
    delta_time_sec: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    speed_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    distance_abs_m: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    ignition: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    # Isolation Forest
    ai_anomaly_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    ai_score_percentile: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    contexte_temporel: Mapped[Optional[str]] = mapped_column(
        Text,
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

    # Croisement règles / IA
    detection_combinee: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    ai_anomaly_flag: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    # Analyse contextuelle
    persistence: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    context_support: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    confidence_level: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    analysis_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Niveau de carburant avant et pendant l'événement
    fuel_before_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    fuel_event_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    recovery_ratio: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Carte
    lien_carte: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Priorisation
    rang_priorite: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    priorite_alerte: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    raison_priorite: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Validation par l'utilisateur
    statut_validation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )