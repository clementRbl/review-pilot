from collections.abc import Callable

import pandas as pd

from review_pilot.data.split import split_train_validation


def test_split_keeps_ten_percent_for_validation(make_reviews: Callable[..., pd.DataFrame]) -> None:
    train, validation = split_train_validation(make_reviews(100))

    assert len(train) == 90
    assert len(validation) == 10


def test_split_is_stratified(make_reviews: Callable[..., pd.DataFrame]) -> None:
    train, validation = split_train_validation(make_reviews(100))

    assert train["label"].mean() == validation["label"].mean() == 0.5


def test_split_is_reproducible(make_reviews: Callable[..., pd.DataFrame]) -> None:
    reviews = make_reviews(100)

    first, _ = split_train_validation(reviews)
    second, _ = split_train_validation(reviews)

    assert first.equals(second)


def test_split_has_no_shared_review(make_reviews: Callable[..., pd.DataFrame]) -> None:
    train, validation = split_train_validation(make_reviews(100))

    assert not set(train["content"]) & set(validation["content"])
