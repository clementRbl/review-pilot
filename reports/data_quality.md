# Rapport de qualité des données

Généré par `uv run python -m review_pilot.data.build` (règles : `notebooks/02_data_cleaning.ipynb`). Tous les contrôles de qualité sont passés.

## Étapes

| Étape | Jeu | Lignes avant | Lignes après | Avis modifiés |
|---|---|---|---|---|
| phrases collées | train | 50000 | 50000 | 11722 |
| HTML | train | 50000 | 50000 | 26 |
| avis non anglais | train | 50000 | 49886 | 0 |
| données personnelles | train | 49886 | 49886 | 51 |
| doublons | train | 49886 | 49885 | 0 |
| phrases collées | test | 10000 | 10000 | 2356 |
| HTML | test | 10000 | 10000 | 2 |
| avis non anglais | test | 10000 | 9975 | 0 |
| données personnelles | test | 9975 | 9975 | 11 |
| doublons | test | 9975 | 9975 | 0 |
| découpage validation | train | 49885 | 44896 | 0 |
| découpage validation | validation | 0 | 4989 | 0 |

« Avis modifiés » : avis dont le titre ou le contenu a changé, sans être retiré.

## Jeux produits

Données brutes : 50000 avis train, 10000 avis test.

| Jeu | Avis | Positifs (%) |
|---|---|---|
| train | 44896 | 49.87 |
| validation | 4989 | 49.87 |
| test | 9975 | 50.25 |
