from sqlalchemy.orm import Session

from app.models.refueling import RefuelingEvent


# Récupérer tous les ravitaillements potentiels
def get_all_refuelings(db: Session):
    return (
        db.query(RefuelingEvent)
        .order_by(RefuelingEvent.event_time.desc())
        .all()
    )