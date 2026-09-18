from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle


# Récupérer tous les véhicules
def get_all_vehicles(db: Session):
    return db.query(Vehicle).order_by(Vehicle.deviceId).all()


# Récupérer un véhicule à partir de son identifiant
def get_vehicle_by_id(db: Session, device_id: int):
    return (
        db.query(Vehicle)
        .filter(Vehicle.deviceId == device_id)
        .first()
    )

# Récupérer les véhicules pour le résumé IA
def get_vehicles_ai_data(db: Session):
    return (
        db.query(Vehicle)
        .order_by(Vehicle.deviceId)
        .all()
    )