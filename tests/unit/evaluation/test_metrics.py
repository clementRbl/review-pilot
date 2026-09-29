import pandas as pd
import pytest

from review_pilot.errors import ThresholdNotFoundError
from review_pilot.evaluation.metrics import (
    best_threshold,
    confusion_counts,
    negative_metrics,
    threshold_table,
)

LABELS = pd.Series([0, 0, 1, 1])


def test_negative_metrics_scores_flagged_reviews_as_negative() -> None:
    metrics = negative_metrics(LABELS, pd.Series([True, False, True, False]))

    assert metrics == {
        "neg_recall": 0.5,
        "neg_precision": 0.5,
        "neg_f1": 0.5,
        "pos_f1": 0.5,
        "accuracy": 0.5,
    }


def test_negative_metrics_when_nothing_is_flagged() -> None:
    metrics = negative_metrics(LABELS, pd.Series([False] * 4))

    assert metrics["neg_recall"] == 0.0
    assert metrics["neg_precision"] == 0.0


def test_confusion_counts_names_each_cell() -> None:
    counts = confusion_counts(LABELS, pd.Series([True, False, True, False]))

    assert counts == {
        "negative_flagged": 1,
        "negative_missed": 1,
        "positive_flagged": 1,
        "positive_kept": 1,
    }


def test_threshold_table_lists_every_integer_threshold() -> None:
    table = threshold_table(pd.Series([3, 1, 0, -1]), LABELS)

    assert list(table.index) == [-1, 0, 1, 2, 3]
    assert table.loc[1, "flagged"] == 2
    assert table.loc[1, "neg_recall"] == 1.0


def test_best_threshold_maximises_recall_above_precision_floor() -> None:
    # Seuil 0 : rappel 100 %, précision 67 % (refusé) ; seuil 1 : rappel et précision 100 %.
    table = threshold_table(pd.Series([3, 1, 0, -1]), LABELS)

    assert best_threshold(table) == 1


def test_best_threshold_prefers_lowest_threshold_on_equal_recall() -> None:
    table = threshold_table(pd.Series([5, 5, -1, -1]), LABELS)

    assert best_threshold(table) == 0


def test_best_threshold_raises_when_no_threshold_is_precise_enough() -> None:
    table = threshold_table(pd.Series([1, 0, 1, 0]), LABELS)

    with pytest.raises(ThresholdNotFoundError, match="85%"):
        best_threshold(table)
