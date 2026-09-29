"""Règle mots-clés : la baseline du projet (voir ``notebooks/03_features_baseline.ipynb``)."""

from collections import Counter
from collections.abc import Iterable
from typing import Final, Self

import pandas as pd

from review_pilot.errors import KeywordListError, NotFittedModelError
from review_pilot.features.text import tokenize
from review_pilot.labels import NEGATIVE, POSITIVE

N_WORDS: Final = 400
# Un mot vu dans moins de 100 avis aurait un ratio extrême par pur hasard.
MIN_REVIEWS: Final = 100
THRESHOLD: Final = 2


def document_frequency(tokens: Iterable[list[str]]) -> Counter[str]:
    """Nombre d'avis qui contiennent chaque mot (un mot répété compte une fois par avis)."""
    return Counter(word for words in tokens for word in set(words))


class KeywordClassifier:
    """Signale un avis comme négatif si (mots négatifs moins mots positifs) atteint le seuil.

    Même interface qu'un modèle scikit-learn : ``fit`` apprend les listes de mots sur le train,
    ``predict`` renvoie les labels prédits.
    """

    def __init__(
        self, n_words: int = N_WORDS, min_reviews: int = MIN_REVIEWS, threshold: int = THRESHOLD
    ) -> None:
        self.n_words = n_words
        self.min_reviews = min_reviews
        self.threshold = threshold
        self.ranking_: pd.Series | None = None

    def fit(self, texts: pd.Series, labels: pd.Series) -> Self:
        """Classe les mots fréquents du plus négatif au plus positif (ratio de fréquences)."""
        tokens = texts.map(tokenize)
        is_negative = labels == NEGATIVE
        counts = pd.DataFrame(
            {
                "negative": pd.Series(document_frequency(tokens[is_negative])),
                "positive": pd.Series(document_frequency(tokens[~is_negative])),
            }
        ).fillna(0)
        frequent = counts[counts["negative"] + counts["positive"] >= self.min_reviews]
        # +1 sur chaque compte : un mot absent d'une classe ne provoque pas de division par zéro.
        negative_share = (frequent["negative"] + 1) / (is_negative.sum() + 1)
        positive_share = (frequent["positive"] + 1) / ((~is_negative).sum() + 1)
        # Arrondi à 2 décimales, comme le notebook : les ratios quasi égaux sont départagés par
        # ordre alphabétique, ce qui rend les listes reproductibles.
        ratio = (negative_share / positive_share).round(2)
        self.ranking_ = ratio.sort_index().sort_values(ascending=False, kind="stable")
        return self

    def keyword_lists(self) -> tuple[set[str], set[str]]:
        """Les ``n_words`` mots les plus négatifs et les ``n_words`` mots les plus positifs."""
        if self.ranking_ is None:
            raise NotFittedModelError(type(self).__name__)
        if 2 * self.n_words > len(self.ranking_):
            # Sinon, les deux listes se chevaucheraient.
            raise KeywordListError(self.n_words, len(self.ranking_))
        words = self.ranking_.index
        return set(words[: self.n_words]), set(words[-self.n_words :])

    def negativity_score(self, texts: pd.Series) -> pd.Series:
        """Nombre de mots négatifs moins nombre de mots positifs, pour chaque avis."""
        negative_words, positive_words = self.keyword_lists()

        def score(words: list[str]) -> int:
            return sum(w in negative_words for w in words) - sum(w in positive_words for w in words)

        return texts.map(tokenize).map(score)

    def predict(self, texts: pd.Series) -> pd.Series:
        """Label prédit de chaque avis : négatif si son score atteint le seuil."""
        flagged = self.negativity_score(texts) >= self.threshold
        return flagged.map({True: NEGATIVE, False: POSITIVE})
