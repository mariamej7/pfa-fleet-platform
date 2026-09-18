from datetime import date as DateType

from pydantic import BaseModel


class FleetDailyResponse(BaseModel):
    deviceId: int
    date: DateType

    nombre_mesures: int
    distance_km: float

    vitesse_moyenne_mesures_kmh: float
    vitesse_max_kmh: float

    fuel_moyen_pct: float

    jour_actif: bool

    annee: int
    mois: int

    jour_semaine: str
    mois_annee: str

    model_config = {
        "from_attributes": True
    }