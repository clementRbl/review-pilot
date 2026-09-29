# ReviewPilot

Pipeline progressif sur des avis clients : ML → RAG → Agent → Fine-tuning → MLOps.

Première brique en cours : un classifieur de sentiment qui **signale au service client les avis
négatifs** (cadre et avancement : [docs/projet-ia.md](docs/projet-ia.md)).

## Prérequis

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- VS Code avec l'extension Jupyter, pour les notebooks

## Démarrer, pas à pas

À faire dans cet ordre, depuis la racine du projet.

**1. Installer** (une fois, puis après chaque changement de dépendances)

```bash
uv sync                      # crée .venv et installe les dépendances
uv run pre-commit install    # active les vérifications automatiques à chaque commit
```

**2. Télécharger les données brutes** (une fois ; environ 1,1 Go de téléchargement la première fois)

```bash
uv run python -m review_pilot.data.download   # → data/raw/train.parquet, data/raw/test.parquet
```

**3. Construire les jeux propres**

```bash
uv run python -m review_pilot.data.build      # → data/processed/{train,val,test}.parquet
                                              #   + reports/data_quality.md
```

**4. Ouvrir les notebooks**, dans l'ordre : dans VS Code, choisir le noyau `.venv`, puis « Run All ».

| Notebook | Phase | Contenu |
|---|---|---|
| [01_eda.ipynb](notebooks/01_eda.ipynb) | exploration | ce que contiennent les avis, ce qui trahit le sentiment |
| [02_data_cleaning.ipynb](notebooks/02_data_cleaning.ipynb) | 2 — données | les règles de nettoyage et le découpage, vérifiés |

Les sorties des notebooks (tableaux, graphiques) ne sont pas versionnées : elles sont effacées
à chaque commit. Relancer « Run All » pour les retrouver.

**5. Vérifier que tout est en ordre**

```bash
uv run pytest --cov                   # tests + couverture
uv run pre-commit run --all-files     # tous les contrôles (format, lint, types, tests…)
```

## Que relancer quand je modifie…

| Je modifie… | Je relance… |
|---|---|
| les dépendances (`pyproject.toml`) | `uv sync` |
| le téléchargement (`data/download.py` : taille de l'échantillon, révision) | étape 2, puis étape 3 |
| une règle de données (`data/clean.py`, `split.py`, `quality.py`) | étape 3, puis les tests (étape 5) |
| un notebook | « Run All » dans le notebook |
| n'importe quel code | étape 5 avant de committer |

## Pour aller plus loin

- [docs/architecture.md](docs/architecture.md) : la « ligne de vie » du projet, qui produit et lit
  quoi, avec un schéma.
- [docs/code.md](docs/code.md) : le guide du code, fichier par fichier et fonction par fonction,
  avec les tests et les notions Python rencontrées.
- [docs/projet-ia.md](docs/projet-ia.md) : le suivi des phases (besoin, métrique, décisions).
- [data/README.md](data/README.md) : la source des données, leur licence et les règles de nettoyage.

## Commandes de développement

```bash
uv run pytest --cov        # tests + couverture
uv run ruff format         # formatage
uv run ruff check --fix    # lint
uv run mypy                # vérification des types (strict)
```
