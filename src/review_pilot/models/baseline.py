"""Mesure les deux baselines sur la validation et les enregistre dans MLflow.

À lancer depuis la racine du projet : ``uv run python -m review_pilot.models.baseline``.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Final

import mlflow
import pandas as pd

from review_pilot.data.build import PROCESSED_DIR, PROCESSED_FILES
from review_pilot.data.clean import full_text
from review_pilot.errors import ThresholdNotFoundError
from review_pilot.evaluation.metrics import (
    PRECISION_MIN,
    best_threshold,
    confusion_counts,
    negative_metrics,
    threshold_table,
)
from review_pilot.labels import NEGATIVE
from review_pilot.models.keywords import MIN_REVIEWS, KeywordClassifier
from review_pilot.tracking import use_experiment

logger = logging.getLogger(__name__)

EXPERIMENT: Final = "phase-3-baseline"
N_WORDS_GRID: Final = (25, 50, 100, 200, 400, 800)


@dataclass(frozen=True, slots=True)
class BaselineResult:
    """Un essai à enregistrer : réglages, scores sur la validation et fichiers joints."""

    name: str
    params: dict[str, int]
    metrics: dict[str, float]
    # Any : frontière avec mlflow.log_dict, qui accepte tout contenu sérialisable en JSON.
    artifacts: dict[str, dict[str, Any]] = field(default_factory=dict)


def load_split(name: str) -> pd.DataFrame:
    """Charge un jeu propre produit par ``review_pilot.data.build``."""
    return pd.read_parquet(PROCESSED_DIR / PROCESSED_FILES[name])


def majority_baseline(train: pd.DataFrame, val: pd.DataFrame) -> BaselineResult:
    """Prédit toujours la classe la plus fréquente du train."""
    majority_label = int(train["label"].mode()[0])
    flagged = pd.Series(majority_label == NEGATIVE, index=val.index)
    return BaselineResult(
        "majority", {"majority_label": majority_label}, negative_metrics(val["label"], flagged)
    )


def keyword_baseline(
    train: pd.DataFrame,
    val: pd.DataFrame,
    n_words_grid: tuple[int, ...],
    min_reviews: int,
) -> BaselineResult:
    """Apprend les listes sur le train, puis choisit leur taille et le seuil sur la validation."""
    model = KeywordClassifier(min_reviews=min_reviews).fit(full_text(train), train["label"])
    val_text = full_text(val)
    best: tuple[float, int, int] | None = None
    for n_words in n_words_grid:
        model.n_words = n_words
        table = threshold_table(model.negativity_score(val_text), val["label"])
        try:
            threshold = best_threshold(table)
        except ThresholdNotFoundError:
            # Cette taille de liste ne tient pas le plancher de précision : elle est écartée.
            continue
        recall = float(table["neg_recall"].to_numpy()[table.index.get_loc(threshold)])
        # Inégalité stricte : à rappel égal, la plus petite liste l'emporte (comme le notebook).
        if best is None or recall > best[0]:
            best = (recall, n_words, threshold)
    if best is None:
        raise ThresholdNotFoundError(PRECISION_MIN)

    _, model.n_words, model.threshold = best
    flagged = model.predict(val_text) == NEGATIVE
    negative_words, positive_words = model.keyword_lists()
    return BaselineResult(
        "keywords",
        {"n_words": model.n_words, "min_reviews": min_reviews, "threshold": model.threshold},
        negative_metrics(val["label"], flagged),
        {
            "keywords.json": {
                "negative": sorted(negative_words),
                "positive": sorted(positive_words),
            },
            "confusion_matrix.json": confusion_counts(val["label"], flagged),
        },
    )


def log_result(result: BaselineResult) -> None:
    """Enregistre un essai dans l'expérience MLflow courante."""
    with mlflow.start_run(run_name=result.name):
        mlflow.set_tag("source", __name__)
        mlflow.log_params({"model": result.name, **result.params})
        mlflow.log_metrics(result.metrics)
        for filename, content in result.artifacts.items():
            mlflow.log_dict(content, filename)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    train, val = load_split("train"), load_split("validation")
    results = [
        majority_baseline(train, val),
        keyword_baseline(train, val, N_WORDS_GRID, MIN_REVIEWS),
    ]
    use_experiment(EXPERIMENT)
    for result in results:
        log_result(result)
        scores = ", ".join(f"{name} {value:.3f}" for name, value in result.metrics.items())
        logger.info("%s %s : %s", result.name, result.params, scores)
    logger.info("runs enregistrés dans l'expérience MLflow « %s »", EXPERIMENT)


if __name__ == "__main__":
    main()
