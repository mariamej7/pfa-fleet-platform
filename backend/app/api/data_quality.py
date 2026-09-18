from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analytics import DataQualityResponse
from app.services.data_quality_service import build_data_quality_summary


router = APIRouter(
    prefix="/api/data-quality",
    tags=["Data Quality"]
)


@router.get(
    "",
    response_model=DataQualityResponse
)
def read_data_quality(
    db: Session = Depends(get_db)
):
    return build_data_quality_summary(db)