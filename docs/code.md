# Guide du code : fichier par fichier

Ce document explique le code de `src/` : ce que fait chaque fichier, chaque fonction, quand ils
sont appelés, et comment ils sont testés. La vue d'ensemble (schéma, commandes, dossiers) est dans
[architecture.md](architecture.md) ; les décisions de chaque phase dans [projet-ia.md](projet-ia.md).

Une section par phase, complétée à la fin de chaque phase.

## Principes communs

- **Seuls les points d'entrée touchent au disque.** Les modules lancés par une commande
  (`download.py`, `build.py`) lisent et écrivent les fichiers. Les autres (`clean.py`,
  `split.py`, `quality.py`) reçoivent un tableau et renvoient un tableau : ce sont des
  **fonctions pures**, testables sans aucun fichier.
- **Notebook d'abord, code ensuite.** Chaque règle est décidée et vérifiée dans un notebook, puis
  recopiée dans `src/` avec des tests. Le code produit exactement les mêmes résultats que le
  notebook.
- **Une règle n'est écrite qu'une fois.** Quand un contrôle vérifie une règle de nettoyage, il
  réutilise la fonction qui nettoie : les deux ne peuvent pas diverger.
- **Tout est reproductible.** Révision du dataset figée, graine du hasard fixée (`SEED = 42`) :
  relancer une commande redonne des fichiers identiques.

## Phase 2 : les données

Deux commandes, lancées depuis la racine du projet :

```text
uv run python -m review_pilot.data.download        ← une fois
        │  télécharge 50 000 + 10 000 avis depuis Hugging Face
        ▼
data/raw/train.parquet, data/raw/test.parquet       ← jamais modifiés ensuite

uv run python -m review_pilot.data.build           ← à chaque changement de règle
        │  build.py est le chef d'orchestre :
        │    1. clean.py    nettoie le train et le test
        │    2. split.py    met 10 % du train de côté (validation)
        │    3. quality.py  vérifie les 3 jeux ; au moindre problème → erreur, rien n'est écrit
        ▼
data/processed/train.parquet, val.parquet, test.parquet
reports/data_quality.md
```

### `data/download.py` : récupérer les données brutes

| Fonction | Rôle |
|---|---|
| `read_shard(filename)` | télécharge **un** fichier du dataset (Hugging Face le découpe en morceaux, les *shards*) et le charge en tableau |
| `sample_rows(frame, n_rows, seed)` | tire `n_rows` lignes au hasard, toujours les mêmes pour une même graine |
| `download_split(files, n_rows)` | prend autant d'avis dans chaque shard (4 shards de train → 12 500 chacun), puis mélange le tout |
| `main()` | le fait pour le train (50 000) et le test (10 000), écrit `data/raw/*.parquet` |

- `REVISION` fige une version précise du dataset, comme un numéro de commit : l'échantillon ne
  change pas si le dataset est mis à jour en amont.
- Les shards sont lus un par un : chacun contient environ 900 000 avis, trop lourd pour les
  charger tous à la fois.
- Le cache de téléchargement va dans `data/.cache/` plutôt que dans `~/.cache` : rien n'est
  écrit en dehors du projet.

### `data/build.py` : le chef d'orchestre

| Fonction | Rôle |
|---|---|
| `build_splits(raw_train, raw_test)` | enchaîne `clean_reviews` (train et test) → `split_train_validation` (train) → `check_quality` (les 3 jeux) |
| `render_report(raw_sizes, splits, reports)` | fabrique le texte Markdown de `reports/data_quality.md` |
| `main()` | lit `data/raw/`, appelle `build_splits`, écrit les 3 parquet et le rapport |

`build.py` ne contient aucune règle : il coordonne. Le test est nettoyé avec les mêmes règles que
le train, mais n'est pas découpé.

### `data/clean.py` : les règles de nettoyage

**Les fonctions qui agissent sur un texte :**

| Fonction | Exemple |
|---|---|
| `fix_glued_sentences` | `"snap.But"` → `"snap. But"` ; `"U.S.A"` reste intact |
| `clean_html` | `"Tom &amp; Jerry<br />"` → `"Tom & Jerry "` ; `<sigh>` est gardé (écrit par le client, il porte une émotion) |
| `mask_personal_data` | `"call 555-123-4567"` → `"call [PHONE]"` ; idem avec `[EMAIL]` |
| `contains_personal_data` | reste-t-il un e-mail ou un téléphone en clair ? |
| `english_share` / `is_english` | part de mots anglais très courants (`the`, `and`, `is`…) ; anglais si au moins 5 % |
| `comparison_key` | `"Great CD!"` → `"greatcd"` : deux avis de même clé sont des quasi-doublons |
| `full_text` | titre + contenu réunis en un seul texte |

**La fonction principale, `clean_reviews(frame, split)`**, applique cinq étapes dans l'ordre du
notebook 02 :

| # | Étape | Sorte | Effet |
|---|---|---|---|
| 1 | phrases collées | réécrit | modifie le titre et le contenu |
| 2 | HTML | réécrit | modifie le titre et le contenu |
| 3 | avis non anglais | retire | supprime des lignes |
| 4 | données personnelles | réécrit | modifie le titre et le contenu |
| 5 | doublons | retire | supprime des lignes ; en dernier, car le nettoyage peut rendre deux avis identiques |

Il n'y a donc que deux sortes d'étapes, chacune avec son aide interne (le `_` au début du nom
signale qu'elle ne sert qu'à l'intérieur du fichier) :

- `_rewrite` applique une fonction à chaque titre et contenu, puis compte les avis modifiés ;
- `_keep` ne garde que les lignes indiquées.

Chaque étape produit un **`StepReport`** : nom de l'étape, jeu, lignes avant, lignes après, avis
modifiés. C'est exactement une ligne du tableau de `reports/data_quality.md`.

### `data/split.py` : mettre la validation de côté

Une seule fonction, `split_train_validation(frame)`, qui appelle `train_test_split` de
scikit-learn :

- `test_size=0.1` : 10 % partent en validation ;
- `stratify=frame["label"]` : même proportion de positifs des deux côtés (49,87 %) ;
- `random_state=42` : reproductible.

### `data/quality.py` : le contrôle final

| Fonction | Rôle |
|---|---|
| `quality_problems(frame)` | renvoie la liste des contrôles qui échouent sur un jeu (liste vide = conforme) : colonnes attendues, labels 0 ou 1, aucune valeur manquante, aucun texte vide, aucun quasi-doublon, aucune donnée personnelle, que de l'anglais |
| `shared_reviews(splits)` | compte les avis présents dans deux jeux à la fois ; il en faut zéro, sinon le modèle serait évalué sur des avis déjà vus (**fuite de données**) |
| `check_quality(splits)` | réunit les deux et lève `DataQualityError` au premier problème : `build` s'arrête avant d'écrire |

`quality.py` réutilise les fonctions de `clean.py` (`is_english`, `comparison_key`,
`contains_personal_data`) : la règle qui nettoie et celle qui vérifie sont la même.

### `errors.py` : les erreurs du projet

- `ReviewPilotError` : la famille de toutes les erreurs du projet.
- `DataQualityError` : les données produites ne respectent pas les contrôles.

Avoir ses propres erreurs permet d'écrire plus tard `except ReviewPilotError` pour traiter les
erreurs métier, sans avaler par accident un vrai bug Python.

### Un avis, du début à la fin

Contenu brut : `"Great sound.Loved it &amp; my kids too<br />Call 555-123-4567"`

| Étape | Résultat |
|---|---|
| phrases collées | `"Great sound. Loved it &amp; my kids too<br />Call 555-123-4567"` |
| HTML | `"Great sound. Loved it & my kids too Call 555-123-4567"` |
| anglais ? | 2 mots courants sur 8 (`it`, `my`) = 25 % ≥ 5 % → gardé |
| données personnelles | `"Great sound. Loved it & my kids too Call [PHONE]"` |
| doublon ? | clé `"greatsoundloveditmykidstoocallphone"` jamais vue → gardé |
| découpage | tiré au hasard : 90 % de chances d'aller en train, 10 % en validation |
| qualité | anglais, pas de téléphone en clair, pas de doublon → conforme |

### Les tests (`tests/unit/data/`)

Un fichier de test par module, nommé `test_<module>.py`. Ils tournent avec `uv run pytest` et
automatiquement à chaque commit (hooks pre-commit).

| Fichier | Ce qu'il vérifie |
|---|---|
| `conftest.py` | pas un test : fournit la fixture `make_reviews`, une fabrique de petits tableaux d'avis factices réutilisée par les autres tests |
| `test_download.py` | échantillon reproductible, shards bien répartis ; Hugging Face est remplacé par un faux (`monkeypatch`) : rien n'est téléchargé |
| `test_clean.py` | chaque règle sur des exemples précis (sigle intact, `<sigh>` gardé…), puis `clean_reviews` en entier |
| `test_split.py` | 90 / 10, proportions égales, reproductible, aucun avis partagé |
| `test_quality.py` | on abîme volontairement un jeu propre de 7 façons et on vérifie que chaque problème est détecté |
| `test_build.py` | la chaîne complète sur 122 faux avis, fichiers écrits dans un dossier temporaire (`tmp_path`) |

### Notions Python rencontrées

| Notion | En une phrase |
|---|---|
| `python -m paquet.module` | exécute un module du projet comme un script |
| `if __name__ == "__main__":` | « si on me lance directement, exécute `main()` ; si on m'importe seulement, ne fais rien » |
| `Final` | indique qu'une constante ne doit pas être réaffectée (vérifié par mypy) |
| `@dataclass(frozen=True, slots=True)` | petite classe qui ne fait que porter des données ; `frozen` la rend non modifiable |
| `re.compile(...)` | prépare une expression régulière (un motif de texte) une fois pour toutes |
| `logging` | messages de suivi (`INFO …`) plutôt que des `print`, réglables en un seul endroit |
| fixture (pytest) | un ingrédient préparé à l'avance, donné à un test qui le demande en paramètre |
| `monkeypatch` (pytest) | remplace temporairement une fonction le temps d'un test |
| `tmp_path` (pytest) | un dossier temporaire neuf pour chaque test, supprimé ensuite |
| `@pytest.mark.parametrize` | lance le même test sur plusieurs cas, un par ligne de la liste |
