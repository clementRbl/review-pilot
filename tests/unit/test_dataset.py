from pathlib import Path

import pandas as pd
import pytest

from review_pilot import dataset


def make_reviews(n_rows: int, offset: int = 0) -> pd.DataFrame:
    ids = range(offset, offset + n_rows)
    return pd.DataFrame(
        {
            "label": [i % 2 for i in ids],
            "title": [f"title {i}" for i in ids],
            "content": [f"content {i}" for i in ids],
        }
    )


@pytest.fixture
def fake_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Remplace le téléchargement Hugging Face par des fichiers parquet locaux de 100 lignes."""
    hub_dir = tmp_path / "hub"
    hub_dir.mkdir()

    def fake_download(repo_id: str, filename: str, **_: object) -> str:
        shard = hub_dir / Path(filename).name
        if not shard.exists():
            offset = 1000 * len(list(hub_dir.iterdir()))
            make_reviews(100, offset).to_parquet(shard, index=False)
        return str(shard)

    monkeypatch.setattr(dataset, "hf_hub_download", fake_download)
    return hub_dir


def test_sample_rows_returns_requested_number_of_rows() -> None:
    sample = dataset.sample_rows(make_reviews(50), n_rows=10, seed=0)

    assert len(sample) == 10


def test_sample_rows_is_reproducible_with_same_seed() -> None:
    reviews = make_reviews(50)

    first = dataset.sample_rows(reviews, n_rows=10, seed=42)
    second = dataset.sample_rows(reviews, n_rows=10, seed=42)

    pd.testing.assert_frame_equal(first, second)


def test_sample_rows_returns_all_rows_when_fewer_than_requested() -> None:
    sample = dataset.sample_rows(make_reviews(5), n_rows=10, seed=0)

    assert len(sample) == 5


def test_sample_rows_resets_index() -> None:
    sample = dataset.sample_rows(make_reviews(50), n_rows=10, seed=0)

    assert list(sample.index) == list(range(10))


@pytest.mark.usefixtures("fake_hub")
def test_download_split_samples_evenly_across_shards() -> None:
    sample = dataset.download_split(("shard-a.parquet", "shard-b.parquet"), n_rows=40)

    from_first_shard = sample["title"].str.removeprefix("title ").astype(int) < 1000
    assert len(sample) == 40
    assert from_first_shard.sum() == 20


@pytest.mark.usefixtures("fake_hub")
def test_main_writes_train_and_test_parquet_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    dataset.main()

    train = pd.read_parquet(tmp_path / "data/raw/train.parquet")
    test = pd.read_parquet(tmp_path / "data/raw/test.parquet")
    assert list(train.columns) == ["label", "title", "content"]
    assert len(train) == 400
    assert len(test) == 100
