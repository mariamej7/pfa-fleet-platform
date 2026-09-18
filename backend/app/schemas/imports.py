from typing import Dict, List, Optional

from pydantic import BaseModel


class DatasetValidationResponse(BaseModel):
    upload_id: str
    extension: str

    nombre_lignes: int
    nombre_colonnes: int
    nombre_vehicules: Optional[int] = None

    debut_periode: Optional[str] = None
    fin_periode: Optional[str] = None

    colonnes_detectees: List[str]

    colonnes_requises: List[str]
    colonnes_requises_manquantes: List[str]

    colonnes_contexte_presentes: List[str]
    colonnes_contexte_manquantes: List[str]

    valeurs_manquantes_pct: Dict[str, float]

    compatible: bool
    niveau_analyse: str
    message: str

    # ========================================================
    # MOTEUR DE TRAITEMENT
    # ========================================================

    # Exemples :
    # "pandas"
    # "spark"
    moteur_recommande: Optional[str] = None

    # Libelle affiche dans l'interface :
    # "Pandas"
    # "Apache Spark"
    moteur_libelle: Optional[str] = None

    # Seuil configure a partir duquel
    # Spark devient le moteur recommande.
    seuil_spark_lignes: Optional[int] = None

    # Explication destinee a l'interface
    # et au suivi du traitement.
    raison_moteur: Optional[str] = None