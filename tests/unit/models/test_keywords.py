import pandas as pd
import pytest

from review_pilot.errors import KeywordListError, NotFittedModelError
from review_pilot.models.keywords import KeywordClassifier, document_frequency

TRAIN_TEXTS = pd.Series(["bad awful", "bad product", "great nice", "great product"])
TRAIN_LABELS = pd.Series([0, 0, 1, 1])


def _fitted(n_words: int = 2, threshold: int = 1) -> KeywordClassifier:
    model = KeywordClassifier(n_words=n_words, min_reviews=1, threshold=threshold)
    return model.fit(TRAIN_TEXTS, TRAIN_LABELS)


def test_document_frequency_counts_each_word_once_per_review() -> None:
    assert document_frequency([["bad", "bad"], ["bad", "good"]]) == {"bad": 2, "good": 1}


def test_fit_ranks_words_from_most_negative_to_most_positive() -> None:
    ranking = _fitted().ranking_

    assert ranking is not None
    assert list(ranking.index) == ["bad", "awful", "product", "nice", "great"]
    assert ranking["bad"] == 3.0  # (2 + 1) / (2 + 1) divisé par (0 + 1) / (2 + 1)


def test_fit_breaks_ties_alphabetically() -> None:
    texts = pd.Series(["zebra apple", "mango"])
    ranking = KeywordClassifier(min_reviews=1).fit(texts, pd.Series([0, 1])).ranking_

    assert ranking is not None
    assert list(ranking.index[:2]) == ["apple", "zebra"]


def test_fit_ignores_rare_words() -> None:
    model = KeywordClassifier(min_reviews=2).fit(TRAIN_TEXTS, TRAIN_LABELS)

    assert model.ranking_ is not None
    assert set(model.ranking_.index) == {"bad", "great", "product"}


def test_keyword_lists_are_learned_from_train_only() -> None:
    model = _fitted()
    model.negativity_score(pd.Series(["terrible terrible awful"]))

    negative_words, positive_words = model.keyword_lists()

    assert negative_words == {"bad", "awful"}
    assert positive_words == {"nice", "great"}
    assert "terrible" not in negative_words | positive_words


def test_keyword_lists_require_enough_frequent_words() -> None:
    with pytest.raises(KeywordListError, match="mots fréquents"):
        _fitted(n_words=3).keyword_lists()


def test_keyword_lists_require_fit() -> None:
    with pytest.raises(NotFittedModelError, match="fit"):
        KeywordClassifier().keyword_lists()


def test_negativity_score_counts_every_occurrence() -> None:
    scores = _fitted().negativity_score(pd.Series(["bad bad great", "nice product", "Awful!"]))

    assert list(scores) == [1, -1, 1]


def test_predict_flags_reviews_whose_score_reaches_threshold() -> None:
    predicted = _fitted(threshold=1).predict(pd.Series(["bad", "bad great", "great"]))

    assert list(predicted) == [0, 1, 1]
