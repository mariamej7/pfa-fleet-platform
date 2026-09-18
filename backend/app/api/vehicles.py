from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.repositories.vehicle_repository import (
    get_all_vehicles,
    get_vehicle_by_id,
)

from app.repositories.fleet_repository import (
    get_vehicle_daily_data,
)

from app.schemas.vehicle import VehicleResponse
from app.schemas.fleet import FleetDailyResponse


router = APIRouter(
    prefix="/api/vehicles",
    tags=["Vehicles"]
)


# Récupérer tous les véhicules
@router.get("", response_model=list[VehicleResponse])
def read_vehicles(db: Session = Depends(get_db)):
    return get_all_vehicles(db)


# Récupérer les données quotidiennes d'un véhicule
@router.get(
    "/{device_id}/daily",
    response_model=list[FleetDailyResponse]
)
def read_vehicle_daily(
    device_id: int,
    db: Session = Depends(get_db)
):
    vehicle = get_vehicle_by_id(db, device_id)

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Véhicule introuvable"
        )

    return get_vehicle_daily_data(db, device_id)


# Récupérer un véhicule précis
@router.get(
    "/{device_id}",
    response_model=VehicleResponse
)
def read_vehicle(
    device_id: int,
    db: Session = Depends(get_db)
):
    vehicle = get_vehicle_by_id(db, device_id)

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Véhicule introuvable"
        )

    return vehicle