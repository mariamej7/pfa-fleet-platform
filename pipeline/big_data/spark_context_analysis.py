import pandas as pd

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from anomaly_detection.context_analysis import (
    analyze_suspicious_context,
)


# ============================================================
# PARAMETRES
# ============================================================

FENETRE_CONTEXTE_MIN = 30

FENETRE_CONTEXTE_SEC = (
    FENETRE_CONTEXTE_MIN
    * 60
)

SUSPICIOUS_EVENT_TYPE = (
    "Baisse suspecte / anomalie potentielle"
)


# ============================================================
# OUTIL
# ============================================================

def dataframe_is_empty(
    df: DataFrame,
) -> bool:
    """
    Vérifie si un DataFrame Spark est vide.
    """

    return (
        df.limit(1).count()
        == 0
    )


# ============================================================
# EXTRACTION DES FENETRES UTILES
# ============================================================

def extract_suspicious_context_spark(
    df_rules: DataFrame,
) -> DataFrame:
    """
    Extrait uniquement les mesures situées
    dans une fenêtre de +/- 30 minutes autour
    des baisses suspectes.

    Les millions de lignes restent dans Spark.
    """

    # --------------------------------------------------------
    # Evénements suspects présents dans le dataset Spark
    # --------------------------------------------------------

    suspicious_points = (
        df_rules
        .filter(
            F.col(
                "event_type"
            )
            ==
            F.lit(
                SUSPICIOUS_EVENT_TYPE
            )
        )
        .select(
            "deviceId",

            F.col(
                "fixTime"
            ).alias(
                "event_time"
            ),
        )
        .filter(
            F.col(
                "event_time"
            ).isNotNull()
        )
        .dropDuplicates(
            [
                "deviceId",
                "event_time",
            ]
        )
    )

    # --------------------------------------------------------
    # Aucun événement
    # --------------------------------------------------------

    if dataframe_is_empty(
        suspicious_points
    ):

        return (
            df_rules.limit(0)
        )

    # --------------------------------------------------------
    # Jointure temporelle
    #
    # Une mesure est conservée uniquement si :
    # - même véhicule ;
    # - comprise entre -30 et +30 minutes.
    # --------------------------------------------------------

    data = (
        df_rules.alias(
            "data"
        )
    )

    events = (
        suspicious_points.alias(
            "events"
        )
    )

    data_timestamp = (
        F.col(
            "data.fixTime"
        ).cast(
            "long"
        )
    )

    event_timestamp = (
        F.col(
            "events.event_time"
        ).cast(
            "long"
        )
    )

    condition = (
        (
            F.col(
                "data.deviceId"
            )
            ==
            F.col(
                "events.deviceId"
            )
        )
        &
        (
            data_timestamp
            >=
            (
                event_timestamp
                -
                F.lit(
                    FENETRE_CONTEXTE_SEC
                )
            )
        )
        &
        (
            data_timestamp
            <=
            (
                event_timestamp
                +
                F.lit(
                    FENETRE_CONTEXTE_SEC
                )
            )
        )
    )

    context = (
        data
        .join(
            F.broadcast(
                events
            ),
            condition,
            how="inner",
        )
        .select(
            "data.*"
        )

        # Plusieurs fenêtres peuvent se chevaucher.
        # Une ligne source ne doit être présente
        # qu'une seule fois dans le dataset transmis
        # à l'analyse Pandas.
        .dropDuplicates()
    )

    return context


# ============================================================
# ANALYSE CONTEXTUELLE HYBRIDE
# ============================================================

def analyze_suspicious_context_spark(
    df_rules: DataFrame,
    suspicious_events: pd.DataFrame,
):
    """
    Version adaptée au chemin Spark.

    Spark :
        filtre les gros volumes.

    Pandas :
        applique la logique métier existante
        uniquement sur les petites fenêtres utiles.
    """

    # --------------------------------------------------------
    # Nombre de dates invalides sur le dataset complet
    # --------------------------------------------------------

    invalid_dates_dataset = int(
        df_rules
        .filter(
            F.col(
                "fixTime"
            ).isNull()
        )
        .count()
    )

    # --------------------------------------------------------
    # Aucun événement suspect
    # --------------------------------------------------------

    if (
        suspicious_events is None
        or suspicious_events.empty
    ):

        empty_context = (
            df_rules
            .limit(0)
            .toPandas()
        )

        results = (
            analyze_suspicious_context(
                empty_context,
                (
                    suspicious_events
                    if suspicious_events
                    is not None
                    else pd.DataFrame()
                ),
            )
        )

        results[
            "summary"
        ][
            "dates_invalides_dataset"
        ] = (
            invalid_dates_dataset
        )

        return results

    # --------------------------------------------------------
    # Extraction Spark des fenêtres
    # --------------------------------------------------------

    context_spark = (
        extract_suspicious_context_spark(
            df_rules
        )
    )

    # --------------------------------------------------------
    # Conversion UNIQUEMENT du sous-ensemble réduit
    # --------------------------------------------------------

    context_pandas = (
        context_spark
        .orderBy(
            "deviceId",
            "fixTime",
        )
        .toPandas()
    )

    # --------------------------------------------------------
    # Réutilisation de la logique Pandas validée
    # --------------------------------------------------------

    results = (
        analyze_suspicious_context(
            context_pandas,
            suspicious_events.copy(),
        )
    )

    # Le filtrage Spark enlève naturellement les lignes
    # dont fixTime est invalide.
    # On remet donc le compteur calculé sur le dataset complet.
    results[
        "summary"
    ][
        "dates_invalides_dataset"
    ] = (
        invalid_dates_dataset
    )

    return results