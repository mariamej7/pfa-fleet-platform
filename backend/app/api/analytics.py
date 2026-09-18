from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analytics import AISummaryResponse
from app.services.analytics_service import build_ai_summary


router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"]
)


@router.get(
    "/ai-summary",
    response_model=AISummaryResponse
)
def read_ai_summary(
    db: Session = Depends(get_db)
):
    return build_ai_summary(db)