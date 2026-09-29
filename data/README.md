# Données

Les données ne sont **pas committées** : seul ce fichier est suivi par Git. Pour les régénérer :

```bash
uv run python -m review_pilot.data.download   # échantillon brut → data/raw/
uv run python -m review_pilot.data.build      # jeux nettoyés → data/processed/
```

Le premier lancement télécharge environ 1,1 Go dans `data/.cache/` (cache Hugging Face).
Une fois `data/raw/` écrit, ce cache peut être supprimé.

## Source

| | |
|---|---|
| Dataset | [`fancyzhx/amazon_polarity`](https://huggingface.co/datasets/fancyzhx/amazon_polarity) |
| Révision | `9d9c45c18f8c3cf1b23a3c27917b60cbf28f3289` (figée) |
| Licence | Apache 2.0 (d'après la fiche du dataset) |
| Langue | Anglais |
| Taille d'origine | 3,6 M d'avis d'entraînement / 400 k de test |

## Organisation

```text
data/
├── README.md         # ce fichier (suivi par Git)
├── .cache/           # cache de téléchargement Hugging Face (supprimable)
├── raw/              # échantillon brut, jamais modifié à la main
│   ├── train.parquet # 50 000 avis
│   └── test.parquet  # 10 000 avis
└── processed/        # jeux nettoyés, recréés par review_pilot.data.build
    ├── train.parquet # 44 896 avis
    ├── val.parquet   # 4 989 avis (validation, 10 % du train, stratifiée)
    └── test.parquet  # 9 975 avis
```

## Nettoyage (`data/processed/`)

Règles décidées et vérifiées dans [notebooks/02_data_cleaning.ipynb](../notebooks/02_data_cleaning.ipynb),
appliquées à l'identique au train et au test :

1. phrases collées séparées (« snap.But » → « snap. But ») ;
2. entités HTML décodées, vraies balises HTML retirées (les marqueurs comme `<sigh>` sont gardés) ;
3. avis non anglais retirés (moins de 5 % de mots anglais très courants) ;
4. e-mails et téléphones masqués (`[EMAIL]`, `[PHONE]`) ;
5. quasi-doublons retirés ;
6. validation : 10 % du train, découpage stratifié, graine 42.

Des contrôles de qualité arrêtent la création des données en cas de problème. Le détail de
chaque étape est dans [reports/data_quality.md](../reports/data_quality.md).

## Échantillonnage

- Train : 12 500 avis tirés au hasard dans chacun des 4 fichiers d'entraînement, puis mélangés.
- Test : 10 000 avis tirés au hasard dans l'unique fichier de test.
- Graine fixe (`42`) : chaque lancement produit exactement le même échantillon.
- Pas de rééquilibrage des classes : la répartition des labels est celle du tirage aléatoire.

## Colonnes

| Colonne | Type | Description |
|---|---|---|
| `label` | int | `0` = négatif, `1` = positif |
| `title` | str | Titre de l'avis |
| `content` | str | Texte de l'avis |
