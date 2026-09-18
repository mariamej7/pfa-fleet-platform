from sqlalchemy.orm import Session

from app.models.fuel_alert import FuelAlert


# Récupérer toutes les alertes
def get_all_alerts(db: Session):
    return (
        db.query(FuelAlert)
        .order_by(
            FuelAlert.rang_priorite,
            FuelAlert.fixTime.desc()
        )
        .all()
    )


# Récupérer une alerte précise
def get_alert_by_id(db: Session, alert_id: str):
    return (
        db.query(FuelAlert)
        .filter(FuelAlert.alert_id == alert_id)
        .first()
    )

# Modifier le statut de validation d'une alerte
def update_alert_status(
    db: Session,
    alert: FuelAlert,
    new_status: str
):
    alert.statut_validation = new_status

    db.commit()
    db.refresh(alert)

    return alert