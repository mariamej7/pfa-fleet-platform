from sqlalchemy.orm import Session

from app.repositories.vehicle_repository import get_vehicles_ai_data


def build_ai_summary(db: Session):
    vehicles = get_vehicles_ai_data(db)

    total_baisses = sum(v.nb_baisses_analysees or 0 for v in vehicles)
    total_candidats = sum(v.nb_candidats_ia or 0 for v in vehicles)
    total_regles = sum(v.nb_alertes_regles or 0 for v in vehicles)
    total_overlap = sum(v.nb_overlap_regles_ia or 0 for v in vehicles)

    # Pourcentage des alertes règles également retrouvées par l'IA
    taux_recouvrement = (
        (total_overlap / total_regles) * 100
        if total_regles > 0
        else 0
    )

    par_vehicule = []

    for vehicle in vehicles:
        par_vehicule.append({
            "deviceId": vehicle.deviceId,
            "nb_baisses_analysees": vehicle.nb_baisses_analysees or 0,
            "nb_candidats_ia": vehicle.nb_candidats_ia or 0,
            "nb_alertes_regles": vehicle.nb_alertes_regles or 0,
            "nb_overlap_regles_ia": vehicle.nb_overlap_regles_ia or 0,
            "nb_alertes_ia_uniquement": vehicle.nb_alertes_ia_uniquement or 0,
            "nb_alertes_regle_uniquement": vehicle.nb_alertes_regle_uniquement or 0,
        })

    return {
        "total_baisses_analysees": total_baisses,
        "total_candidats_ia": total_candidats,
        "total_alertes_regles": total_regles,
        "total_overlap_regles_ia": total_overlap,
        "taux_recouvrement_pct": round(taux_recouvrement, 2),
        "par_vehicule": par_vehicule,
    }