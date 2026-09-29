"""Découpage en mots et TF-IDF, décidés dans ``notebooks/03_features_baseline.ipynb``."""

import re
from typing import Final

from sklearn.feature_extraction.text import TfidfVectorizer

# Minuscules, suites de lettres et d'apostrophes : « don't » reste un seul mot.
TOKEN: Final = re.compile(r"[a-z']+")

# Mots seuls et paires de mots : « not good » devient un terme à part, distinct de « good ».
NGRAM_RANGE: Final = (1, 2)
# Un terme vu dans moins de 5 avis du train n'apprend rien au modèle.
MIN_DF: Final = 5


def tokenize(text: str) -> list[str]:
    """Découpe un texte en mots, comme dans l'EDA."""
    return TOKEN.findall(text.lower())


def build_vectorizer() -> TfidfVectorizer:
    """TF-IDF du projet : appris sur le train seul (``fit``), appliqué au reste (``transform``)."""
    # sublinear_tf : un terme répété 10 fois dans un avis ne pèse pas 10 fois plus.
    return TfidfVectorizer(ngram_range=NGRAM_RANGE, min_df=MIN_DF, sublinear_tf=True)
