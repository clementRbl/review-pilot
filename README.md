# ReviewPilot

Pipeline progressif sur des avis clients : ML → RAG → Agent → Fine-tuning → MLOps.

## Prérequis

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
uv sync
uv run pre-commit install
```

## Données

```bash
uv run python -m review_pilot.dataset
```

Télécharge un échantillon reproductible du dataset Amazon Polarity dans `data/raw/`.
Détails (source, licence, colonnes) : [data/README.md](data/README.md).

## Utilisation

```bash
uv run review-pilot
```

## Développement

```bash
uv run pytest --cov        # tests + couverture
uv run ruff format         # formatage
uv run ruff check --fix    # lint
uv run mypy                # vérification des types (strict)
uv run pre-commit run --all-files
```
