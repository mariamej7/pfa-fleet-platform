from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VehicleResponse(BaseModel):

    deviceId: int

    # Volume de données
    nombre_mesures: Optional[int] = None

    # Période observée
    debut_periode: Optional[datetime] = None
    fin_periode: Optional[datetime] = None

    jours_calendaires_periode: Optional[int] = None
    jours_avec_donnees: Optional[int] = None
    jours_actifs: Optional[int] = None

    taux_couverture_jours_pct: Optional[float] = None

    # Performance
    distance_km: Optional[float] = None
    distance_moyenne_par_jour_actif_km: Optional[float] = None

    vitesse_moyenne_mesures_kmh: Optional[float] = None
    vitesse_moyenne_en_mouvement_kmh: Optional[float] = None
    vitesse_max_kmh: Optional[float] = None

    # Carburant
    fuel_moyen_pct: Optional[float] = None
    fuel_min_pct: Optional[float] = None
    fuel_max_pct: Optional[float] = None

    # Ravitaillements potentiels
    nb_ravitaillements_potentiels: Optional[int] = None
    hausse_moyenne_refuel_pct: Optional[float] = None
    hausse_max_refuel_pct: Optional[float] = None

    # Baisses détectées par les règles
    nb_baisses_suspectes: Optional[int] = None
    baisse_moyenne_suspecte_pct: Optional[float] = None
    baisse_max_suspecte_pct: Optional[float] = None

    # Qualité du signal carburant
    nb_incoherences_fuel: Optional[int] = None
    pct_incoherences_fuel: Optional[float] = None

    # Isolation Forest
    nb_baisses_analysees: Optional[int] = None
    nb_candidats_ia: Optional[int] = None

    # Comparaison règles / IA
    nb_alertes_regles: Optional[int] = None
    nb_overlap_regles_ia: Optional[int] = None
    nb_alertes_ia_uniquement: Optional[int] = None
    nb_alertes_regle_uniquement: Optional[int] = None

    model_config = {
        "from_attributes": True
    }