from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analytics import DashboardSummaryResponse
from app.services.dashboard_service import get_dashboard_summary


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse
)
def read_dashboard_summary(
    db: Session = Depends(get_db)
):
    summary = get_dashboard_summary(db)

    if summary is None:
        raise HTTPException(
            status_code=404,
            detail="Résumé global introuvable"
        )

    return summary