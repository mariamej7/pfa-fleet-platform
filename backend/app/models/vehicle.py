from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Vehicle(Base):
    __tablename__ = "dim_vehicles"

    # Identifiant unique du véhicule
    deviceId: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # Nombre de mesures
    nombre_mesures: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )

    # Période étudiée
    debut_periode: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    fin_periode: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    jours_calendaires_periode: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    jours_avec_donnees: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    jours_actifs: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    taux_couverture_jours_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Distance
    distance_km: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    distance_moyenne_par_jour_actif_km: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Vitesse
    vitesse_moyenne_mesures_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    vitesse_moyenne_en_mouvement_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    vitesse_max_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Carburant
    fuel_moyen_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    fuel_min_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    fuel_max_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Ravitaillements potentiels
    nb_ravitaillements_potentiels: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    hausse_moyenne_refuel_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    hausse_max_refuel_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Baisses suspectes
    nb_baisses_suspectes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    baisse_moyenne_suspecte_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    baisse_max_suspecte_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Qualité du signal carburant
    nb_incoherences_fuel: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    pct_incoherences_fuel: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Isolation Forest / alertes
    nb_baisses_analysees: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    nb_candidats_ia: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    nb_alertes_regles: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    nb_overlap_regles_ia: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    nb_alertes_ia_uniquement: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    nb_alertes_regle_uniquement: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )