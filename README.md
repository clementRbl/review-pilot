# ReviewPilot

Progressive pipeline on customer reviews: ML → RAG → Agent → Fine-tuning → MLOps.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
uv run pre-commit install
```

## Usage

```bash
uv run review-pilot
```

## Development

```bash
uv run pytest --cov        # tests + coverage
uv run ruff format         # format
uv run ruff check --fix    # lint
uv run mypy                # type check (strict)
uv run pre-commit run --all-files
```
