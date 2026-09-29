# Architecture : la ligne de vie de ReviewPilot

Ce document montre comment les fichiers du projet s'enchaînent, des avis bruts jusqu'au modèle :
qui produit quoi, qui lit quoi, et avec quelle commande. Il est mis à jour à la fin de chaque
phase du projet (suivi des phases : [projet-ia.md](projet-ia.md)).

## Vue d'ensemble

Les flèches pleines existent déjà ; les flèches en pointillé sont les phases à venir.

```mermaid
flowchart TD
    HF[("Hugging Face<br/>fancyzhx/amazon_polarity<br/>(révision figée)")]
    RAW["data/raw/<br/>train.parquet · test.parquet"]
    EDA["notebooks/01_eda.ipynb<br/>exploration"]
    NB02["notebooks/02_data_cleaning.ipynb<br/>règles de nettoyage"]
    PROC["data/processed/<br/>train · val · test"]
    REPORT["reports/data_quality.md"]
    P3["Phase 3<br/>features + baseline"]
    P4["Phase 4<br/>modélisation"]
    P5["Phase 5<br/>évaluation sur le test"]
    P6["Phase 6<br/>explicabilité"]
    P7["Phase 7<br/>industrialisation"]

    subgraph BUILD ["review_pilot.data.build"]
        CLEAN["clean.py<br/>nettoyage"] --> SPLIT["split.py<br/>validation 10 %"] --> QUALITY["quality.py<br/>contrôles"]
    end

    HF -->|"review_pilot.data.download"| RAW
    RAW -->|lu par| EDA
    RAW -->|lu par| NB02
    NB02 -.->|"règles recopiées et testées"| BUILD
    RAW -->|lu par| BUILD
    BUILD --> PROC
    BUILD --> REPORT
    PROC -.-> P3 -.-> P4 -.-> P5 -.-> P6 -.-> P7
```

## Les étapes, dans l'ordre

| # | Étape | Commande | Lit | Produit | Code |
|---|---|---|---|---|---|
| 1 | Télécharger l'échantillon | `uv run python -m review_pilot.data.download` | Hugging Face (révision figée) | `data/raw/train.parquet` (50 000 avis), `data/raw/test.parquet` (10 000 avis), cache `data/.cache/` | `src/review_pilot/data/download.py` |
| 2 | Explorer les données (EDA) | notebook, « Run All » | `data/raw/` | des conclusions (aucun fichier) | `notebooks/01_eda.ipynb` |
| 3 | Décider le nettoyage | notebook, « Run All » | `data/raw/` | des règles vérifiées (aucun fichier) | `notebooks/02_data_cleaning.ipynb` |
| 4 | Construire les jeux propres | `uv run python -m review_pilot.data.build` | `data/raw/` | `data/processed/{train,val,test}.parquet`, `reports/data_quality.md` | `src/review_pilot/data/build.py` |
| 5 | Features + baseline | *(phase 3, à venir)* | `data/processed/` | | |

Les étapes 2 et 3 n'écrivent rien : elles servent à **comprendre et décider**. Seules les étapes 1
et 4 produisent des fichiers, et elles se relancent à l'identique (graine fixe, révision figée).

## Rôle de chaque dossier

```text
review-pilot/
├── src/review_pilot/        # le code du projet (testé)
│   ├── __init__.py          # point d'entrée « review-pilot » (provisoire)
│   ├── errors.py            # exceptions du projet (ReviewPilotError, DataQualityError)
│   └── data/                # tout ce qui touche aux données
│       ├── download.py      # étape 1 : échantillon brut depuis Hugging Face
│       ├── clean.py         # règles de nettoyage (phrases collées, HTML, langue, données perso, doublons)
│       ├── split.py         # découpage train / validation stratifié
│       ├── quality.py       # contrôles de qualité, bloquants
│       └── build.py         # étape 4 : enchaîne clean → split → quality, écrit les fichiers
├── notebooks/               # une par phase : on comprend et on décide ici, avant le code
│   ├── 01_eda.ipynb
│   └── 02_data_cleaning.ipynb
├── data/                    # jamais versionné (sauf data/README.md)
│   ├── raw/                 # données brutes, jamais modifiées
│   ├── processed/           # jeux propres, recréés par l'étape 4
│   └── .cache/              # cache de téléchargement (supprimable)
├── reports/                 # rapports produits par le code (data_quality.md)
├── tests/unit/              # tests du code de src/ (un fichier par module)
└── docs/
    ├── projet-ia.md         # suivi des phases : cadre, décisions, avancement
    └── architecture.md      # ce document
```

## Qui appelle quoi dans `src/`

```mermaid
flowchart LR
    build["data/build.py"] --> clean["data/clean.py"]
    build --> split["data/split.py"]
    build --> quality["data/quality.py"]
    quality --> clean
    quality --> errors["errors.py"]
    download["data/download.py"]
```

`download.py` est indépendant : il ne sert qu'à produire `data/raw/`. Les notebooks n'importent
pas le code de `src/` : leur code est volontairement recopié, pour rester lisible et garder la
trace du raisonnement.

## Les règles qui tiennent l'ensemble

- **Les données brutes ne sont jamais modifiées** : tout part de `data/raw/`, et tout le reste
  se recrée avec les commandes ci-dessus.
- **Le test reste intact jusqu'à la phase 5** : il est nettoyé avec les mêmes règles que le
  train, mais aucun modèle n'est évalué dessus avant.
- **Notebook d'abord, code ensuite** : chaque phase est décidée dans un notebook, validée, puis
  recopiée dans `src/` avec des tests. Le code doit produire exactement les mêmes résultats que
  le notebook (vérifié pour la phase 2 : jeux identiques ligne à ligne).
- **Les contrôles de qualité sont bloquants** : si un jeu produit ne les respecte pas,
  `build` s'arrête avec une `DataQualityError` au lieu d'écrire des données abîmées.
- **Ne sont versionnés que le code, les notebooks (sans leurs sorties) et les documents** :
  les données, le cache et les futurs modèles restent en local.
