from sqlalchemy.orm import Session

from app.models.fleet_daily import FleetDaily

from app.models.fleet_summary import FleetSummary


# Récupérer les données journalières d'un véhicule
def get_vehicle_daily_data(db: Session, device_id: int):
    return (
        db.query(FleetDaily)
        .filter(FleetDaily.deviceId == device_id)
        .order_by(FleetDaily.date)
        .all()
    )


# Récupérer le résumé global de la flotte
def get_fleet_summary(db: Session):
    return (
        db.query(FleetSummary)
        .order_by(FleetSummary.date_generation.desc())
        .first()
    )