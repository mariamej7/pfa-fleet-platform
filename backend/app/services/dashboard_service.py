from sqlalchemy.orm import Session

from app.repositories.fleet_repository import get_fleet_summary


def get_dashboard_summary(db: Session):
    return get_fleet_summary(db)