from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    date_generation: Optional[datetime] = None

    nombre_vehicules: Optional[float] = None
    nombre_total_mesures: Optional[float] = None
    distance_totale_km: Optional[float] = None

    nb_ravitaillements_potentiels: Optional[int] = None
    nb_alertes_regles: Optional[int] = None
    nb_candidats_ia: Optional[int] = None
    nb_regle_et_ia: Optional[int] = None
    nb_alertes_finales_uniques: Optional[int] = None
    nb_alertes_p1_critiques: Optional[int] = None

    nb_incoherences_fuel: Optional[float] = None

    model_config = {
        "from_attributes": True
    }


class VehicleAISummary(BaseModel):
    deviceId: int
    nb_baisses_analysees: int
    nb_candidats_ia: int
    nb_alertes_regles: int
    nb_overlap_regles_ia: int
    nb_alertes_ia_uniquement: int
    nb_alertes_regle_uniquement: int


class AISummaryResponse(BaseModel):
    total_baisses_analysees: int
    total_candidats_ia: int
    total_alertes_regles: int
    total_overlap_regles_ia: int

    taux_recouvrement_pct: float

    par_vehicule: list[VehicleAISummary]


class VehicleDataQuality(BaseModel):
    deviceId: int
    taux_couverture_jours_pct: float
    nb_incoherences_fuel: int
    pct_incoherences_fuel: float


class DataQualityResponse(BaseModel):
    total_incoherences_fuel: int
    nb_vehicules_avec_incoherences: int
    par_vehicule: list[VehicleDataQuality]