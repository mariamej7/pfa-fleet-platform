from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.repositories.alert_repository import (
    get_all_alerts,
    get_alert_by_id,
    update_alert_status,
)

from app.schemas.alert import (
    FuelAlertResponse,
    AlertStatusUpdate,
)


router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"]
)


# Récupérer toutes les alertes
@router.get("", response_model=list[FuelAlertResponse])
def read_alerts(db: Session = Depends(get_db)):
    return get_all_alerts(db)


# Récupérer une alerte précise
@router.get("/{alert_id}", response_model=FuelAlertResponse)
def read_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    alert = get_alert_by_id(db, alert_id)

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alerte introuvable"
        )

    return alert


# Modifier le statut d'une alerte
@router.patch(
    "/{alert_id}/status",
    response_model=FuelAlertResponse
)
def change_alert_status(
    alert_id: str,
    data: AlertStatusUpdate,
    db: Session = Depends(get_db)
):
    alert = get_alert_by_id(db, alert_id)

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alerte introuvable"
        )

    allowed_statuses = [
        "À vérifier",
        "Confirmée",
        "Faux positif",
        "Ignorée",
    ]

    if data.statut_validation not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Statut de validation invalide"
        )

    return update_alert_status(
        db,
        alert,
        data.statut_validation
    )