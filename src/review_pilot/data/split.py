"""Découpage du train en train et validation."""

from typing import Final

import pandas as pd
from sklearn.model_selection import train_test_split

VALIDATION_SIZE: Final = 0.1
SEED: Final = 42


def split_train_validation(
    frame: pd.DataFrame, validation_size: float = VALIDATION_SIZE, seed: int = SEED
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Met de côté une validation, en gardant la même proportion de labels des deux côtés."""
    parts: list[pd.DataFrame] = train_test_split(
        frame, test_size=validation_size, stratify=frame["label"], random_state=seed
    )
    train, validation = parts
    return train.reset_index(drop=True), validation.reset_index(drop=True)
