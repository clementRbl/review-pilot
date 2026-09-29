import pandas as pd

from review_pilot.features.text import build_vectorizer, tokenize


def test_tokenize_lowercases_and_keeps_apostrophes() -> None:
    assert tokenize("Don't BUY it, 2 stars!") == ["don't", "buy", "it", "stars"]


def test_vectorizer_keeps_word_pairs() -> None:
    vectorizer = build_vectorizer().fit(pd.Series(["not good at all"] * 5))

    assert "not good" in vectorizer.vocabulary_


def test_vectorizer_ignores_terms_seen_in_fewer_than_five_reviews() -> None:
    texts = pd.Series(["great product"] * 5 + ["rare word"] * 4)

    vectorizer = build_vectorizer().fit(texts)

    assert "great" in vectorizer.vocabulary_
    assert "rare" not in vectorizer.vocabulary_


def test_vectorizer_learns_vocabulary_from_train_only() -> None:
    train = pd.Series(["great product"] * 5)
    val = pd.Series(["terrible thing"] * 5)
    vectorizer = build_vectorizer().fit(train)

    transformed = vectorizer.transform(val)

    assert not {"terrible", "thing"} & set(vectorizer.vocabulary_)
    assert transformed.nnz == 0
