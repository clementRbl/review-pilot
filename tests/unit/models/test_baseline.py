from pathlib import Path

import mlflow
import pandas as pd
import pytest

from review_pilot.errors import ThresholdNotFoundError
from review_pilot.models import baseline


def _reviews(n_rows: int) -> pd.DataFrame:
    """Avis négatifs avec « bad awful », positifs avec « great nice », en alternance."""
    return pd.DataFrame(
        {
            "label": [i % 2 for i in range(n_rows)],
            "title": ["review"] * n_rows,
            "content": [
                f"bad awful thing number{i}" if i % 2 == 0 else f"great nice thing number{i}"
                for i in range(n_rows)
            ],
        }
    )


def test_majority_baseline_flags_everything_when_negatives_dominate() -> None:
    train = _reviews(5)  # 3 négatifs, 2 positifs

    result = baseline.majority_baseline(train, _reviews(4))

    assert result.params == {"majority_label": 0}
    assert result.metrics["neg_recall"] == 1.0
    assert result.metrics["neg_precision"] == 0.5


def test_keyword_baseline_picks_list_size_and_threshold_on_validation() -> None:
    result = baseline.keyword_baseline(_reviews(20), _reviews(10), (1, 2), min_reviews=2)

    # À rappel égal (100 %), la plus petite liste et le plus petit seuil l'emportent.
    assert result.params == {"n_words": 1, "min_reviews": 2, "threshold": 0}
    assert result.metrics["neg_recall"] == 1.0
    assert result.artifacts["confusion_matrix.json"]["negative_missed"] == 0
    assert result.artifacts["keywords.json"] == {"negative": ["awful"], "positive": ["nice"]}


def test_keyword_baseline_skips_list_sizes_that_are_not_precise_enough() -> None:
    val = _reviews(10)
    val["label"] = 1 - val["label"]  # labels inversés : aucun seuil ne peut être précis

    with pytest.raises(ThresholdNotFoundError):
        baseline.keyword_baseline(_reviews(20), val, (1,), min_reviews=2)


def test_main_logs_both_baselines_in_mlflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    processed = tmp_path / "data/processed"
    processed.mkdir(parents=True)
    _reviews(20).to_parquet(processed / "train.parquet", index=False)
    _reviews(10).to_parquet(processed / "val.parquet", index=False)
    monkeypatch.setattr(baseline, "N_WORDS_GRID", (1,))
    monkeypatch.setattr(baseline, "MIN_REVIEWS", 2)

    baseline.main()

    runs = mlflow.search_runs(experiment_names=[baseline.EXPERIMENT], output_format="list")
    assert sorted(run.info.run_name for run in runs) == ["keywords", "majority"]
    assert (tmp_path / "mlartifacts").is_dir()
