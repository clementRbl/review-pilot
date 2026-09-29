from collections.abc import Callable

import pandas as pd
import pytest

from review_pilot.data.quality import check_quality, quality_problems, shared_reviews
from review_pilot.errors import DataQualityError


def test_clean_reviews_have_no_problem(make_reviews: Callable[..., pd.DataFrame]) -> None:
    assert quality_problems(make_reviews()) == []


def _set_first(column: str, value: str | int | None) -> Callable[[pd.DataFrame], pd.DataFrame]:
    def corrupt(frame: pd.DataFrame) -> pd.DataFrame:
        frame.loc[0, column] = value
        return frame

    return corrupt


def _duplicate_first(frame: pd.DataFrame) -> pd.DataFrame:
    frame.loc[1, "content"] = frame.loc[0, "content"]
    return frame


@pytest.mark.parametrize(
    ("corrupt", "problem"),
    [
        (lambda frame: frame.rename(columns={"title": "summary"}), "colonnes attendues"),
        (_set_first("label", 2), "labels 0 ou 1"),
        (_set_first("title", None), "aucune valeur manquante"),
        (_set_first("content", "   "), "aucun texte vide"),
        (_duplicate_first, "aucun quasi-doublon"),
        (
            _set_first("content", "It is the best, write to me at a@b.com"),
            "aucune donnée personnelle",
        ),
        (_set_first("content", "Este libro es muy bueno"), "que de l'anglais"),
    ],
    ids=["colonnes", "label", "manquant", "vide", "doublon", "e-mail", "langue"],
)
def test_quality_problems_detects_each_problem(
    make_reviews: Callable[..., pd.DataFrame],
    corrupt: Callable[[pd.DataFrame], pd.DataFrame],
    problem: str,
) -> None:
    assert problem in quality_problems(corrupt(make_reviews()))


def test_shared_reviews_counts_reviews_in_two_splits(
    make_reviews: Callable[..., pd.DataFrame],
) -> None:
    reviews = make_reviews(10)

    shared = shared_reviews({"train": reviews.iloc[:6], "test": reviews.iloc[4:]})

    assert shared == {"train et test": 2}


def test_check_quality_raises_on_shared_review(make_reviews: Callable[..., pd.DataFrame]) -> None:
    reviews = make_reviews(10)

    with pytest.raises(DataQualityError, match="avis en commun"):
        check_quality({"train": reviews.iloc[:6], "test": reviews.iloc[4:]})


def test_check_quality_accepts_clean_splits(make_reviews: Callable[..., pd.DataFrame]) -> None:
    reviews = make_reviews(10)

    check_quality({"train": reviews.iloc[:5], "test": reviews.iloc[5:]})
