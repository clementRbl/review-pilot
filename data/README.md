# Données

Les données ne sont **pas committées** : seul ce fichier est suivi par Git. Pour les régénérer :

```bash
uv run python -m review_pilot.dataset
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
└── processed/        # données transformées (étapes suivantes)
```

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
