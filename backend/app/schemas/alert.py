from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FuelAlertResponse(BaseModel):
    alert_id: str

    deviceId: Optional[int] = None
    fixTime: Optional[datetime] = None

    alert_type: Optional[str] = None
    source_detection: Optional[str] = None
    suspicious_event_id: Optional[str] = None

    fuelLevel: Optional[float] = None
    drop_abs_pct: Optional[float] = None
    delta_time_sec: Optional[float] = None

    speed_kmh: Optional[float] = None
    distance_abs_m: Optional[float] = None
    ignition: Optional[bool] = None

    ai_anomaly_score: Optional[float] = None
    ai_score_percentile: Optional[float] = None

    contexte_temporel: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    detection_combinee: Optional[str] = None
    ai_anomaly_flag: Optional[bool] = None

    persistence: Optional[str] = None
    context_support: Optional[str] = None
    confidence_level: Optional[str] = None
    analysis_reason: Optional[str] = None

    fuel_before_pct: Optional[float] = None
    fuel_event_pct: Optional[float] = None
    recovery_ratio: Optional[float] = None

    lien_carte: Optional[str] = None

    rang_priorite: Optional[int] = None
    priorite_alerte: Optional[str] = None
    raison_priorite: Optional[str] = None
    statut_validation: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class AlertStatusUpdate(BaseModel):
    statut_validation: str