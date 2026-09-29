from collections.abc import Callable

import pandas as pd
import pytest


@pytest.fixture
def make_reviews() -> Callable[..., pd.DataFrame]:
    """Fabrique un petit jeu d'avis anglais valides ; les textes fournis remplacent les défauts."""

    def factory(n_rows: int = 20, contents: list[str] | None = None) -> pd.DataFrame:
        texts = contents or [
            f"This is review number {i} and it is not bad at all" for i in range(n_rows)
        ]
        return pd.DataFrame(
            {
                "label": [i % 2 for i in range(len(texts))],
                "title": [f"title {i}" for i in range(len(texts))],
                "content": texts,
            }
        )

    return factory
