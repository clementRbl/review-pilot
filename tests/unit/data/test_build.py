from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from review_pilot.data import build


def _raw_reviews(
    make_reviews: Callable[..., pd.DataFrame], n_rows: int, offset: int
) -> pd.DataFrame:
    contents = [f"This is review number {offset + i} and it is not bad" for i in range(n_rows)]
    contents[0] = "Este producto es muy bueno y lo recomiendo"
    return make_reviews(contents=contents)


def test_build_splits_cleans_splits_and_checks_quality(
    make_reviews: Callable[..., pd.DataFrame],
) -> None:
    raw_train = _raw_reviews(make_reviews, 101, offset=0)
    raw_test = _raw_reviews(make_reviews, 21, offset=1000)

    splits, reports = build.build_splits(raw_train, raw_test)

    assert {name: len(frame) for name, frame in splits.items()} == {
        "train": 90,
        "validation": 10,
        "test": 20,
    }
    assert reports[-1].step == "découpage validation"


def test_render_report_lists_steps_and_splits(make_reviews: Callable[..., pd.DataFrame]) -> None:
    splits, reports = build.build_splits(
        _raw_reviews(make_reviews, 101, offset=0), _raw_reviews(make_reviews, 21, offset=1000)
    )

    report = build.render_report({"train": 101, "test": 21}, splits, reports)

    assert "| avis non anglais | train | 101 | 100 | 0 |" in report
    assert "| validation | 10 | 50.00 |" in report


def test_main_writes_processed_files_and_report(
    make_reviews: Callable[..., pd.DataFrame], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    raw_dir = tmp_path / "data/raw"
    raw_dir.mkdir(parents=True)
    _raw_reviews(make_reviews, 101, offset=0).to_parquet(raw_dir / "train.parquet", index=False)
    _raw_reviews(make_reviews, 21, offset=1000).to_parquet(raw_dir / "test.parquet", index=False)

    build.main()

    assert len(pd.read_parquet(tmp_path / "data/processed/val.parquet")) == 10
    assert (tmp_path / "reports/data_quality.md").read_text().startswith("# Rapport de qualité")
