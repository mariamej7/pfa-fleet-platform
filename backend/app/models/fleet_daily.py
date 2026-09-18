from datetime import date as DateType
from typing import Optional

from sqlalchemy import Boolean, Date, Float, Integer, BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FleetDaily(Base):
    __tablename__ = "fact_fleet_daily"

    # Clé primaire composée : véhicule + date
    deviceId: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    date: Mapped[DateType] = mapped_column(
        Date,
        primary_key=True,
    )

    # Nombre de mesures du jour
    nombre_mesures: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )

    # Distance parcourue
    distance_km: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Vitesse
    vitesse_moyenne_mesures_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    vitesse_max_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Niveau moyen de carburant
    fuel_moyen_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Indique si le véhicule a été actif ce jour-là
    jour_actif: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    # Colonnes calendrier
    annee: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    mois: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    jour_semaine: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    mois_annee: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )