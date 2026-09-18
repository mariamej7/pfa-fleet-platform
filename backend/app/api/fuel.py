from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.fuel_repository import get_all_refuelings
from app.schemas.fuel import RefuelingEventResponse


router = APIRouter(
    prefix="/api/fuel",
    tags=["Fuel"]
)


@router.get(
    "/refuelings",
    response_model=list[RefuelingEventResponse]
)
def read_refuelings(
    db: Session = Depends(get_db)
):
    return get_all_refuelings(db)