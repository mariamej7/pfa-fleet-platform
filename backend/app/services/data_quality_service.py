from sqlalchemy.orm import Session

from app.repositories.vehicle_repository import get_all_vehicles


def build_data_quality_summary(db: Session):
    vehicles = get_all_vehicles(db)

    total_incoherences = sum(
        vehicle.nb_incoherences_fuel or 0
        for vehicle in vehicles
    )

    nb_vehicules_avec_incoherences = sum(
        1
        for vehicle in vehicles
        if (vehicle.nb_incoherences_fuel or 0) > 0
    )

    par_vehicule = []

    for vehicle in vehicles:
        par_vehicule.append({
            "deviceId": vehicle.deviceId,
            "taux_couverture_jours_pct": vehicle.taux_couverture_jours_pct or 0,
            "nb_incoherences_fuel": vehicle.nb_incoherences_fuel or 0,
            "pct_incoherences_fuel": vehicle.pct_incoherences_fuel or 0,
        })

    return {
        "total_incoherences_fuel": total_incoherences,
        "nb_vehicules_avec_incoherences": nb_vehicules_avec_incoherences,
        "par_vehicule": par_vehicule,
    }