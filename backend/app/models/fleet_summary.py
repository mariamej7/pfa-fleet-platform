from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FleetSummary(Base):
    __tablename__ = "fleet_summary"

    # Date de génération des résultats
    # Utilisée comme identifiant SQLAlchemy de la ligne de synthèse
    date_generation: Mapped[datetime] = mapped_column(
        DateTime,
        primary_key=True,
        nullable=False,
    )

    # Nombre total de véhicules analysés
    nombre_vehicules: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Nombre total de mesures préparées
    nombre_total_mesures: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Distance totale estimée
    distance_totale_km: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Ravitaillements potentiels
    nb_ravitaillements_potentiels: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Alertes détectées par les règles
    nb_alertes_regles: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Candidats détectés par Isolation Forest
    nb_candidats_ia: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Événements détectés à la fois par les règles et l'IA
    nb_regle_et_ia: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Nombre final d'événements uniques à investiguer
    nb_alertes_finales_uniques: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Nombre d'événements de priorité P1
    nb_alertes_p1_critiques: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Mesures fuelLevel hors plage cohérente
    nb_incoherences_fuel: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )