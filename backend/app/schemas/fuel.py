from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RefuelingEventResponse(BaseModel):
    event_id: str

    refuel_episode_id: Optional[str] = None
    deviceId: Optional[int] = None

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    duration_sec: Optional[float] = None
    n_steps: Optional[int] = None

    start_fuel_pct: Optional[float] = None
    end_fuel_pct: Optional[float] = None
    total_delta_fuel_pct: Optional[float] = None

    max_speed_kmh: Optional[float] = None
    mean_speed_kmh: Optional[float] = None

    event_time: Optional[datetime] = None

    event_category: Optional[str] = None
    source_detection: Optional[str] = None

    variation_fuel_pct: Optional[float] = None
    fuel_level_pct: Optional[float] = None

    model_config = {
        "from_attributes": True
    }