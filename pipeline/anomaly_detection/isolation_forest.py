from typing import Dict

import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler


# ============================================================
# PARAMETRES IA
# ============================================================

FEATURES_IA = [
    "drop_abs_pct",
    "log_delta_time",
    "speed_kmh",
    "log_distance_abs",
    "ignition_ai",
    "fuelLevel",
]

# Top 1 % des observations les plus atypiques
# de chaque vehicule.
SEUIL_PERCENTILE_IA = 99.0

# Nombre minimal de baisses necessaires
# pour entrainer un modele propre a un vehicule.
MIN_BAISSES_POUR_MODELE = 50


# ============================================================
# COLONNES DES SORTIES IA
# ============================================================

MODEL_SUMMARY_COLUMNS = [
    "deviceId",
    "nb_baisses_analysees",
    "nb_candidats_ia",
    "seuil_percentile_ia",
]

VEHICLE_SUMMARY_COLUMNS = [
    "deviceId",
    "nb_baisses_analysees",
    "nb_candidats_ia",
    "nb_alertes_regles",
    "nb_overlap_regles_ia",
]

COMPARISON_COLUMNS = [
    "suspicious_event_id",
    "deviceId",
    "fixTime",
    "fuelLevel",
    "delta_fuel",
    "drop_abs_pct",
    "delta_time_sec",
    "speed_kmh",
    "distance_abs_m",
    "ignition",
    "ai_anomaly_score",
    "ai_score_percentile",
    "ai_anomaly_flag",
]


# ============================================================
# PETITS OUTILS
# ============================================================

def ensure_columns(
    dataframe: pd.DataFrame,
    columns,
) -> pd.DataFrame:
    """
    Ajoute les colonnes absentes avec des valeurs vides.
    """

    result = dataframe.copy()

    for column in columns:

        if column not in result.columns:
            result[column] = pd.NA

    return result


def build_empty_ai_scores(
    ai_candidates: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construit une table IA vide mais avec le schema attendu.
    """

    ai_scores = ai_candidates.copy()

    if "ai_anomaly_score" not in ai_scores.columns:
        ai_scores[
            "ai_anomaly_score"
        ] = pd.Series(
            index=ai_scores.index,
            dtype="float64",
        )

    if "ai_score_percentile" not in ai_scores.columns:
        ai_scores[
            "ai_score_percentile"
        ] = pd.Series(
            index=ai_scores.index,
            dtype="float64",
        )

    if "ai_anomaly_flag" not in ai_scores.columns:
        ai_scores[
            "ai_anomaly_flag"
        ] = pd.Series(
            index=ai_scores.index,
            dtype="bool",
        )

    return ai_scores


# ============================================================
# PREPARATION DES BAISSES POUR L'IA
# ============================================================

def prepare_ai_candidates(
    df_rules: pd.DataFrame,
    suspicious_events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare les diminutions de carburant valides
    qui seront analysees par Isolation Forest.

    Reprend la logique du Notebook 4.
    """

    df_ai = df_rules.copy()

    required_columns = [
        "deviceId",
        "fixTime",
        "fuelLevel",
        "delta_fuel",
        "delta_time_sec",
        "speed_kmh",
        "delta_odometer_m",
        "ignition",
        "flag_incoherence_fuel",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df_ai.columns
    ]

    if missing_columns:

        raise ValueError(
            "Impossible d'executer Isolation Forest. "
            f"Colonnes manquantes : {missing_columns}"
        )

    # --------------------------------------------------------
    # Conversion numerique robuste
    # --------------------------------------------------------

    numeric_columns = [
        "fuelLevel",
        "delta_fuel",
        "delta_time_sec",
        "speed_kmh",
        "delta_odometer_m",
    ]

    for column in numeric_columns:

        df_ai[
            column
        ] = pd.to_numeric(
            df_ai[
                column
            ],
            errors="coerce",
        )

    # --------------------------------------------------------
    # Conversion de ignition en 0 / 1
    # --------------------------------------------------------

    if pd.api.types.is_bool_dtype(
        df_ai[
            "ignition"
        ]
    ):

        df_ai[
            "ignition_ai"
        ] = (
            df_ai[
                "ignition"
            ]
            .astype(float)
        )

    else:

        ignition_text = (
            df_ai[
                "ignition"
            ]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        df_ai[
            "ignition_ai"
        ] = (
            ignition_text.map(
                {
                    "true": 1.0,
                    "false": 0.0,
                    "1": 1.0,
                    "0": 0.0,
                }
            )
        )

        df_ai[
            "ignition_ai"
        ] = (
            df_ai[
                "ignition_ai"
            ]
            .fillna(
                pd.to_numeric(
                    df_ai[
                        "ignition"
                    ],
                    errors="coerce",
                )
            )
            .fillna(0.0)
        )

    # --------------------------------------------------------
    # Conversion du flag d'incoherence
    # --------------------------------------------------------

    flag_incoherence = (
        df_ai[
            "flag_incoherence_fuel"
        ]
        .fillna(False)
    )

    if (
        flag_incoherence.dtype
        == object
    ):

        flag_incoherence = (
            flag_incoherence
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("true")
        )

    else:

        flag_incoherence = (
            flag_incoherence
            .astype(bool)
        )

    # --------------------------------------------------------
    # Associer les alertes detectees par regles
    # --------------------------------------------------------

    df_ai[
        "suspicious_event_id"
    ] = pd.NA

    if (
        suspicious_events is not None
        and not suspicious_events.empty
    ):

        common_indexes = (
            df_ai.index.intersection(
                suspicious_events.index
            )
        )

        df_ai.loc[
            common_indexes,
            "suspicious_event_id",
        ] = suspicious_events.loc[
            common_indexes,
            "suspicious_event_id",
        ]

    # --------------------------------------------------------
    # Selection des baisses valides
    # --------------------------------------------------------

    ai_mask = (
        df_ai[
            "fuelLevel"
        ].between(
            0,
            100,
        )
        &
        (~flag_incoherence)
        &
        (
            df_ai[
                "delta_fuel"
            ] < 0
        )
        &
        df_ai[
            "delta_time_sec"
        ].notna()
        &
        df_ai[
            "speed_kmh"
        ].notna()
        &
        df_ai[
            "delta_odometer_m"
        ].notna()
    )

    ai_candidates = (
        df_ai.loc[
            ai_mask
        ]
        .copy()
    )

    # --------------------------------------------------------
    # Feature 1 :
    # amplitude absolue de la baisse
    # --------------------------------------------------------

    ai_candidates[
        "drop_abs_pct"
    ] = (
        -ai_candidates[
            "delta_fuel"
        ]
    )

    # --------------------------------------------------------
    # Feature 2 :
    # temps en logarithme
    # --------------------------------------------------------

    ai_candidates[
        "log_delta_time"
    ] = np.log1p(
        ai_candidates[
            "delta_time_sec"
        ].clip(
            lower=0,
            upper=24 * 3600,
        )
    )

    # --------------------------------------------------------
    # Distance absolue
    # --------------------------------------------------------

    ai_candidates[
        "distance_abs_m"
    ] = (
        ai_candidates[
            "delta_odometer_m"
        ]
        .abs()
    )

    # --------------------------------------------------------
    # Feature 4 :
    # distance en logarithme
    # --------------------------------------------------------

    ai_candidates[
        "log_distance_abs"
    ] = np.log1p(
        ai_candidates[
            "distance_abs_m"
        ].clip(
            upper=100000
        )
    )

    return ai_candidates


# ============================================================
# ENTRAINEMENT DES MODELES
# ============================================================

def train_isolation_forest_models(
    ai_candidates: pd.DataFrame,
) -> Dict:
    """
    Entraine un Isolation Forest separe
    pour chaque vehicule.

    Un vehicule qui ne possede pas assez de baisses
    est ignore sans faire planter le pipeline.
    """

    results = []
    model_summaries = []

    models = {}
    scalers = {}

    ignored_vehicles = []

    # --------------------------------------------------------
    # Analyse vehicule par vehicule
    # --------------------------------------------------------

    for device_id, group in (
        ai_candidates
        .groupby(
            "deviceId"
        )
    ):

        # Variables reellement utilisables.

        X = (
            group[
                FEATURES_IA
            ]
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
            .dropna()
        )

        model_group = (
            group.loc[
                X.index
            ]
            .copy()
        )

        # ----------------------------------------------------
        # Pas assez de donnees pour ce vehicule
        # ----------------------------------------------------

        if (
            len(X)
            < MIN_BAISSES_POUR_MODELE
        ):

            ignored_vehicles.append(
                {
                    "deviceId":
                        device_id,

                    "nb_baisses_exploitables":
                        int(
                            len(X)
                        ),
                }
            )

            continue

        # ----------------------------------------------------
        # Mise a l'echelle robuste
        # ----------------------------------------------------

        scaler = (
            RobustScaler()
        )

        X_scaled = (
            scaler.fit_transform(
                X
            )
        )

        # ----------------------------------------------------
        # Isolation Forest
        # ----------------------------------------------------

        model = IsolationForest(
            n_estimators=300,
            contamination="auto",
            random_state=42,
            n_jobs=-1,
        )

        model.fit(
            X_scaled
        )

        # score_samples :
        # plus petit = plus atypique.
        # On inverse le signe :
        # plus grand = plus atypique.

        anomaly_score = (
            -model.score_samples(
                X_scaled
            )
        )

        model_group[
            "ai_anomaly_score"
        ] = anomaly_score

        # ----------------------------------------------------
        # Percentile PAR VEHICULE
        # ----------------------------------------------------

        model_group[
            "ai_score_percentile"
        ] = (
            pd.Series(
                anomaly_score,
                index=
                    model_group.index,
            )
            .rank(
                method="average",
                pct=True,
            )
            * 100
        )

        # ----------------------------------------------------
        # Top 1 %
        # ----------------------------------------------------

        model_group[
            "ai_anomaly_flag"
        ] = (
            model_group[
                "ai_score_percentile"
            ]
            >= SEUIL_PERCENTILE_IA
        )

        models[
            device_id
        ] = model

        scalers[
            device_id
        ] = scaler

        results.append(
            model_group
        )

        model_summaries.append(
            {
                "deviceId":
                    device_id,

                "nb_baisses_analysees":
                    int(
                        len(
                            model_group
                        )
                    ),

                "nb_candidats_ia":
                    int(
                        model_group[
                            "ai_anomaly_flag"
                        ].sum()
                    ),

                "seuil_percentile_ia":
                    SEUIL_PERCENTILE_IA,
            }
        )

    # --------------------------------------------------------
    # Aucun modele n'a pu etre entraine
    # --------------------------------------------------------

    if not results:

        ai_scores = (
            build_empty_ai_scores(
                ai_candidates
                .iloc[0:0]
                .copy()
            )
        )

        ai_model_summary = (
            pd.DataFrame(
                columns=
                    MODEL_SUMMARY_COLUMNS
            )
        )

        return {
            "ai_scores":
                ai_scores,

            "ai_model_summary":
                ai_model_summary,

            "models":
                models,

            "scalers":
                scalers,

            "ignored_vehicles":
                ignored_vehicles,
        }

    # --------------------------------------------------------
    # Au moins un modele a ete entraine
    # --------------------------------------------------------

    ai_scores = (
        pd.concat(
            results,
            ignore_index=False,
        )
        .sort_values(
            [
                "deviceId",
                "fixTime",
            ]
        )
        .copy()
    )

    ai_model_summary = (
        pd.DataFrame(
            model_summaries,
            columns=
                MODEL_SUMMARY_COLUMNS,
        )
    )

    return {
        "ai_scores":
            ai_scores,

        "ai_model_summary":
            ai_model_summary,

        "models":
            models,

        "scalers":
            scalers,

        "ignored_vehicles":
            ignored_vehicles,
    }


# ============================================================
# CANDIDATS IA
# ============================================================

def build_ai_top_candidates(
    ai_scores: pd.DataFrame,
) -> pd.DataFrame:
    """
    Conserve uniquement le top 1 %
    des baisses les plus atypiques.
    """

    ai_scores = (
        build_empty_ai_scores(
            ai_scores
        )
    )

    ai_flag = (
        ai_scores[
            "ai_anomaly_flag"
        ]
        .fillna(False)
        .astype(bool)
    )

    ai_top = (
        ai_scores.loc[
            ai_flag
        ]
        .copy()
    )

    # --------------------------------------------------------
    # Contexte temporel
    # --------------------------------------------------------

    ai_top[
        "contexte_temporel"
    ] = np.where(
        ai_top[
            "delta_time_sec"
        ] > 1800,
        (
            "Coupure > 30 min : "
            "interprétation prudente"
        ),
        "Intervalle <= 30 min",
    )

    # --------------------------------------------------------
    # Detection par les regles
    # --------------------------------------------------------

    ai_top[
        "detectee_par_regle"
    ] = (
        ai_top[
            "suspicious_event_id"
        ]
        .notna()
    )

    return ai_top


# ============================================================
# RESUME IA PAR VEHICULE
# ============================================================

def build_ai_vehicle_summary(
    ai_scores: pd.DataFrame,
) -> pd.DataFrame:
    """
    Resume les resultats IA par vehicule.
    """

    if ai_scores.empty:

        return pd.DataFrame(
            columns=
                VEHICLE_SUMMARY_COLUMNS
        )

    summary = (
        ai_scores
        .groupby(
            "deviceId"
        )
        .agg(
            nb_baisses_analysees=(
                "deviceId",
                "size",
            ),

            nb_candidats_ia=(
                "ai_anomaly_flag",
                "sum",
            ),

            nb_alertes_regles=(
                "suspicious_event_id",
                lambda values:
                    values
                    .notna()
                    .sum(),
            ),
        )
        .reset_index()
    )

    overlap = (
        ai_scores[
            (
                ai_scores[
                    "ai_anomaly_flag"
                ]
                .fillna(False)
                .astype(bool)
            )
            &
            (
                ai_scores[
                    "suspicious_event_id"
                ]
                .notna()
            )
        ]
        .groupby(
            "deviceId"
        )
        .size()
        .rename(
            "nb_overlap_regles_ia"
        )
        .reset_index()
    )

    summary = (
        summary.merge(
            overlap,
            on="deviceId",
            how="left",
        )
    )

    integer_columns = [
        "nb_baisses_analysees",
        "nb_candidats_ia",
        "nb_alertes_regles",
        "nb_overlap_regles_ia",
    ]

    for column in integer_columns:

        summary[
            column
        ] = (
            summary[
                column
            ]
            .fillna(0)
            .astype(int)
        )

    return (
        summary[
            VEHICLE_SUMMARY_COLUMNS
        ]
    )


# ============================================================
# COMPARAISON REGLES / IA
# ============================================================

def compare_rules_and_ai(
    ai_scores: pd.DataFrame,
    suspicious_events: pd.DataFrame = None,
) -> Dict:
    """
    Compare les alertes des regles
    avec leur classement Isolation Forest.

    Les alertes des regles restent disponibles
    meme si aucun modele IA n'a pu etre entraine.

    Le taux obtenu est un taux de recouvrement,
    PAS une accuracy.
    """

    ai_scores = (
        ensure_columns(
            ai_scores,
            COMPARISON_COLUMNS,
        )
    )

    # --------------------------------------------------------
    # Alertes regles presentes dans les scores IA
    # --------------------------------------------------------

    rules_vs_ai = (
        ai_scores[
            ai_scores[
                "suspicious_event_id"
            ].notna()
        ][
            COMPARISON_COLUMNS
        ]
        .copy()
    )

    # --------------------------------------------------------
    # Recuperer les alertes regles non scorees par l'IA
    # --------------------------------------------------------

    if (
        suspicious_events is not None
        and not suspicious_events.empty
    ):

        rule_events = (
            suspicious_events.copy()
        )

        # Distance absolue, si elle n'existe pas deja.

        if (
            "distance_abs_m"
            not in rule_events.columns
        ):

            if (
                "delta_odometer_m"
                in rule_events.columns
            ):

                rule_events[
                    "distance_abs_m"
                ] = (
                    pd.to_numeric(
                        rule_events[
                            "delta_odometer_m"
                        ],
                        errors="coerce",
                    )
                    .abs()
                )

            else:

                rule_events[
                    "distance_abs_m"
                ] = np.nan

        # Colonnes IA absentes pour une alerte
        # qui n'a pas pu etre scoree.

        rule_events[
            "ai_anomaly_score"
        ] = np.nan

        rule_events[
            "ai_score_percentile"
        ] = np.nan

        rule_events[
            "ai_anomaly_flag"
        ] = False

        rule_events = (
            ensure_columns(
                rule_events,
                COMPARISON_COLUMNS,
            )
        )

        # IDs deja presents dans les scores IA.

        existing_ids = set(
            rules_vs_ai[
                "suspicious_event_id"
            ]
            .dropna()
            .astype(str)
            .tolist()
        )

        missing_rules = (
            rule_events[
                ~rule_events[
                    "suspicious_event_id"
                ]
                .astype(str)
                .isin(
                    existing_ids
                )
            ][
                COMPARISON_COLUMNS
            ]
            .copy()
        )

        if not missing_rules.empty:

            rules_vs_ai = (
                pd.concat(
                    [
                        rules_vs_ai,
                        missing_rules,
                    ],
                    ignore_index=True,
                )
            )

    # --------------------------------------------------------
    # Securite sur les doublons
    # --------------------------------------------------------

    if not rules_vs_ai.empty:

        rules_vs_ai = (
            rules_vs_ai
            .drop_duplicates(
                subset=[
                    "suspicious_event_id"
                ],
                keep="first",
            )
            .copy()
        )

    # --------------------------------------------------------
    # Regle + IA / Regle uniquement
    # --------------------------------------------------------

    if rules_vs_ai.empty:

        rules_vs_ai[
            "detection_combinee"
        ] = pd.Series(
            dtype="object"
        )

    else:

        ai_flag = (
            rules_vs_ai[
                "ai_anomaly_flag"
            ]
            .fillna(False)
            .astype(bool)
        )

        rules_vs_ai[
            "ai_anomaly_flag"
        ] = ai_flag

        rules_vs_ai[
            "detection_combinee"
        ] = np.where(
            ai_flag,
            "Règle + IA",
            "Règle uniquement",
        )

        rules_vs_ai = (
            rules_vs_ai
            .sort_values(
                "ai_score_percentile",
                ascending=False,
                na_position="last",
            )
            .reset_index(
                drop=True
            )
        )

    # --------------------------------------------------------
    # Resume
    # --------------------------------------------------------

    nb_rule_alerts = int(
        len(
            rules_vs_ai
        )
    )

    if (
        "ai_anomaly_flag"
        in rules_vs_ai.columns
    ):

        nb_overlap = int(
            rules_vs_ai[
                "ai_anomaly_flag"
            ]
            .fillna(False)
            .astype(bool)
            .sum()
        )

    else:

        nb_overlap = 0

    if (
        nb_rule_alerts > 0
    ):

        overlap_rate = (
            nb_overlap
            / nb_rule_alerts
            * 100
        )

    else:

        # Aucun evenement regle :
        # pas de comparaison possible.
        # On conserve 0 pour garder une sortie
        # exploitable par l'API.
        overlap_rate = 0.0

    return {
        "rules_vs_ai_comparison":
            rules_vs_ai,

        "nb_alertes_regles":
            nb_rule_alerts,

        "nb_overlap_regles_ia":
            nb_overlap,

        "taux_recouvrement_pct":
            float(
                overlap_rate
            ),
    }


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def detect_ai_anomalies(
    df_rules: pd.DataFrame,
    suspicious_events: pd.DataFrame,
) -> Dict:
    """
    Execute toute l'etape Isolation Forest.

    Si aucun vehicule ne possede suffisamment
    de baisses exploitables, le pipeline continue
    avec des sorties IA vides mais structurees.
    """

    # --------------------------------------------------------
    # 1. Preparer les baisses valides
    # --------------------------------------------------------

    ai_candidates = (
        prepare_ai_candidates(
            df_rules,
            suspicious_events,
        )
    )

    # --------------------------------------------------------
    # 2. Entrainer les modeles
    # --------------------------------------------------------

    training_results = (
        train_isolation_forest_models(
            ai_candidates
        )
    )

    ai_scores = (
        training_results[
            "ai_scores"
        ]
    )

    # --------------------------------------------------------
    # 3. Top 1 % IA
    # --------------------------------------------------------

    ai_top = (
        build_ai_top_candidates(
            ai_scores
        )
    )

    # --------------------------------------------------------
    # 4. Resume par vehicule
    # --------------------------------------------------------

    vehicle_summary = (
        build_ai_vehicle_summary(
            ai_scores
        )
    )

    # --------------------------------------------------------
    # 5. Comparaison regles / IA
    # --------------------------------------------------------

    comparison = (
        compare_rules_and_ai(
            ai_scores,
            suspicious_events,
        )
    )

    # --------------------------------------------------------
    # 6. Candidats IA uniquement
    # --------------------------------------------------------

    ai_only_candidates = (
        ai_top[
            ai_top[
                "suspicious_event_id"
            ].isna()
        ]
        .copy()
        .sort_values(
            "ai_score_percentile",
            ascending=False,
        )
    )

    # --------------------------------------------------------
    # 7. Resume global
    # --------------------------------------------------------

    global_summary = {
        "nombre_baisses_analysees":
            int(
                len(
                    ai_scores
                )
            ),

        "nombre_candidats_ia":
            int(
                ai_scores[
                    "ai_anomaly_flag"
                ]
                .fillna(False)
                .astype(bool)
                .sum()
            ),

        "nombre_alertes_regles":
            comparison[
                "nb_alertes_regles"
            ],

        "nombre_overlap_regles_ia":
            comparison[
                "nb_overlap_regles_ia"
            ],

        "taux_recouvrement_pct":
            comparison[
                "taux_recouvrement_pct"
            ],

        "nombre_candidats_ia_uniquement":
            int(
                len(
                    ai_only_candidates
                )
            ),

        "nombre_modeles_entraines":
            int(
                len(
                    training_results[
                        "models"
                    ]
                )
            ),
    }

    return {
        "ai_candidates":
            ai_candidates,

        "ai_scores":
            ai_scores,

        "ai_top_candidates":
            ai_top,

        "ai_model_summary":
            training_results[
                "ai_model_summary"
            ],

        "ai_vehicle_summary":
            vehicle_summary,

        "rules_vs_ai_comparison":
            comparison[
                "rules_vs_ai_comparison"
            ],

        "ai_only_candidates":
            ai_only_candidates,

        "summary":
            global_summary,

        "models":
            training_results[
                "models"
            ],

        "scalers":
            training_results[
                "scalers"
            ],

        "ignored_vehicles":
            training_results[
                "ignored_vehicles"
            ],
    }