"""Recrée les jeux train / validation / test propres à partir des données brutes.

À lancer depuis la racine du projet : ``uv run python -m review_pilot.data.build``.
"""

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Final

import pandas as pd

from review_pilot.data.clean import StepReport, clean_reviews
from review_pilot.data.quality import check_quality
from review_pilot.data.split import split_train_validation

logger = logging.getLogger(__name__)

RAW_DIR: Final = Path("data/raw")
PROCESSED_DIR: Final = Path("data/processed")
REPORT_PATH: Final = Path("reports/data_quality.md")
PROCESSED_FILES: Final = {
    "train": "train.parquet",
    "validation": "val.parquet",
    "test": "test.parquet",
}


def build_splits(
    raw_train: pd.DataFrame, raw_test: pd.DataFrame
) -> tuple[dict[str, pd.DataFrame], list[StepReport]]:
    """Nettoie les données brutes, découpe la validation et vérifie la qualité des trois jeux."""
    train, train_reports = clean_reviews(raw_train, "train")
    test, test_reports = clean_reviews(raw_test, "test")
    rows_before = len(train)
    train, validation = split_train_validation(train)
    split_reports = [
        StepReport("découpage validation", "train", rows_before, len(train), 0),
        StepReport("découpage validation", "validation", 0, len(validation), 0),
    ]
    splits = {"train": train, "validation": validation, "test": test}
    check_quality(splits)
    return splits, [*train_reports, *test_reports, *split_reports]


def render_report(
    raw_sizes: Mapping[str, int], splits: Mapping[str, pd.DataFrame], reports: list[StepReport]
) -> str:
    """Rapport de qualité en Markdown : effet de chaque étape, puis taille finale des jeux."""
    lines = [
        "# Rapport de qualité des données",
        "",
        "Généré par `uv run python -m review_pilot.data.build` (règles : "
        "`notebooks/02_data_cleaning.ipynb`). Tous les contrôles de qualité sont passés.",
        "",
        "## Étapes",
        "",
        "| Étape | Jeu | Lignes avant | Lignes après | Avis modifiés |",
        "|---|---|---|---|---|",
        *(
            f"| {r.step} | {r.split} | {r.rows_before} | {r.rows_after} | {r.reviews_changed} |"
            for r in reports
        ),
        "",
        "« Avis modifiés » : avis dont le titre ou le contenu a changé, sans être retiré.",
        "",
        "## Jeux produits",
        "",
        f"Données brutes : {raw_sizes['train']} avis train, {raw_sizes['test']} avis test.",
        "",
        "| Jeu | Avis | Positifs (%) |",
        "|---|---|---|",
        *(
            f"| {name} | {len(frame)} | {frame['label'].mean() * 100:.2f} |"
            for name, frame in splits.items()
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raw_train = pd.read_parquet(RAW_DIR / "train.parquet")
    raw_test = pd.read_parquet(RAW_DIR / "test.parquet")
    splits, reports = build_splits(raw_train, raw_test)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in splits.items():
        frame.to_parquet(PROCESSED_DIR / PROCESSED_FILES[name], index=False)
        logger.info("%s : %d avis écrits", name, len(frame))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw_sizes = {"train": len(raw_train), "test": len(raw_test)}
    REPORT_PATH.write_text(render_report(raw_sizes, splits, reports), encoding="utf-8")
    logger.info("rapport de qualité écrit dans %s", REPORT_PATH)


if __name__ == "__main__":
    main()
