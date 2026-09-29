"""Métriques du projet (phase 1) : rappel négatif sous un plancher de précision négative."""

from typing import Final

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from review_pilot.errors import ThresholdNotFoundError
from review_pilot.labels import NEGATIVE

PRECISION_MIN: Final = 0.85


def negative_metrics(labels: pd.Series, flagged: pd.Series) -> dict[str, float]:
    """Scores d'une prédiction où chaque avis signalé (``flagged``) est prédit négatif."""
    truly_negative = labels == NEGATIVE
    return {
        "neg_recall": float(recall_score(truly_negative, flagged, zero_division=0)),
        "neg_precision": float(precision_score(truly_negative, flagged, zero_division=0)),
        "neg_f1": float(f1_score(truly_negative, flagged, zero_division=0)),
        "pos_f1": float(f1_score(~truly_negative, ~flagged, zero_division=0)),
        "accuracy": float(accuracy_score(truly_negative, flagged)),
    }


def confusion_counts(labels: pd.Series, flagged: pd.Series) -> dict[str, int]:
    """Les quatre cases de la matrice de confusion, nommées dans le vocabulaire du projet."""
    truly_negative = labels == NEGATIVE
    return {
        "negative_flagged": int((truly_negative & flagged).sum()),
        "negative_missed": int((truly_negative & ~flagged).sum()),
        "positive_flagged": int((~truly_negative & flagged).sum()),
        "positive_kept": int((~truly_negative & ~flagged).sum()),
    }


def threshold_table(score: pd.Series, labels: pd.Series) -> pd.DataFrame:
    """Scores obtenus pour chaque seuil entier possible : un avis est signalé si score ≥ seuil."""
    rows = [
        {"threshold": threshold, "flagged": int((score >= threshold).sum())}
        | negative_metrics(labels, score >= threshold)
        for threshold in range(int(score.min()), int(score.max()) + 1)
    ]
    return pd.DataFrame(rows).set_index("threshold")


def best_threshold(table: pd.DataFrame) -> int:
    """Le seuil au meilleur rappel négatif parmi ceux qui gardent la précision au plancher."""
    allowed = table[table["neg_precision"] >= PRECISION_MIN]
    if allowed.empty:
        raise ThresholdNotFoundError(PRECISION_MIN)
    # argmax renvoie la première position du maximum : à rappel égal, le seuil le plus bas.
    return int(allowed.index.to_numpy()[allowed["neg_recall"].to_numpy().argmax()])
