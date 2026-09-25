"""Télécharge un échantillon reproductible du dataset Amazon Polarity dans data/raw/.

À lancer depuis la racine du projet : ``uv run python -m review_pilot.dataset``.
"""

import logging
from pathlib import Path
from typing import Final

import pandas as pd
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

REPO_ID: Final = "fancyzhx/amazon_polarity"
# Commit figé : l'échantillon reste identique même si le dataset change en amont.
REVISION: Final = "9d9c45c18f8c3cf1b23a3c27917b60cbf28f3289"
TRAIN_FILES: Final = tuple(f"amazon_polarity/train-0000{i}-of-00004.parquet" for i in range(4))
TEST_FILES: Final = ("amazon_polarity/test-00000-of-00001.parquet",)
TRAIN_ROWS: Final = 50_000
TEST_ROWS: Final = 10_000
SEED: Final = 42

RAW_DIR: Final = Path("data/raw")
# Dans le projet plutôt que dans ~/.cache/huggingface : rien n'est écrit en dehors.
CACHE_DIR: Final = Path("data/.cache")


def sample_rows(frame: pd.DataFrame, n_rows: int, seed: int) -> pd.DataFrame:
    """Renvoie un échantillon aléatoire reproductible de ``n_rows`` lignes (toutes si moins)."""
    return frame.sample(n=min(n_rows, len(frame)), random_state=seed).reset_index(drop=True)


def read_shard(filename: str) -> pd.DataFrame:
    """Télécharge un fichier parquet du dataset (mis en cache) et le charge."""
    path = hf_hub_download(
        REPO_ID, filename, repo_type="dataset", revision=REVISION, cache_dir=CACHE_DIR
    )
    return pd.read_parquet(path)


def download_split(files: tuple[str, ...], n_rows: int) -> pd.DataFrame:
    """Tire ``n_rows`` lignes réparties également entre les fichiers, puis les mélange."""
    # Un fichier à la fois : chacun contient ~900k avis, trop lourd pour charger les quatre.
    per_file = n_rows // len(files)
    samples = [sample_rows(read_shard(filename), per_file, SEED) for filename in files]
    return sample_rows(pd.concat(samples), n_rows, SEED)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    splits = (("train", TRAIN_FILES, TRAIN_ROWS), ("test", TEST_FILES, TEST_ROWS))
    for split, files, n_rows in splits:
        output = RAW_DIR / f"{split}.parquet"
        download_split(files, n_rows).to_parquet(output, index=False)
        logger.info("%s: sample written to %s", split, output)


if __name__ == "__main__":
    main()
