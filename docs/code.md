# Guide du code : fichier par fichier

Ce document explique le code de `src/` : ce que fait chaque fichier, chaque fonction, quand ils
sont appelés, et comment ils sont testés. La vue d'ensemble (schéma, commandes, dossiers) est dans
[architecture.md](architecture.md) ; les décisions de chaque phase dans [projet-ia.md](projet-ia.md).

Une section par phase, complétée à la fin de chaque phase.

## Principes communs

- **Seuls les points d'entrée touchent au disque.** Les modules lancés par une commande
  (`download.py`, `build.py`, `baseline.py`) lisent et écrivent les fichiers. Les autres
  (`clean.py`, `split.py`, `quality.py`, `keywords.py`, `metrics.py`…) reçoivent des données et
  renvoient des données : ce sont des **fonctions pures**, testables sans aucun fichier.
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

## Phase 3 : features et baseline

Une commande, lancée depuis la racine du projet, après `review_pilot.data.build` :

```text
uv run python -m review_pilot.models.baseline
        │  baseline.py est le chef d'orchestre :
        │    1. lit data/processed/train.parquet et val.parquet (jamais le test)
        │    2. classe majoritaire : prédit toujours la classe la plus fréquente du train
        │    3. règle mots-clés : keywords.py apprend les listes sur le train,
        │       puis metrics.py choisit la taille des listes et le seuil sur la validation
        │    4. tracking.py ouvre l'expérience MLflow « phase-3-baseline »
        ▼
2 runs MLflow (majority, keywords) : réglages, scores, fichiers joints
  → mlflow.db (runs, réglages, scores) et mlartifacts/ (keywords.json, confusion_matrix.json)
```

Résultat attendu, identique au notebook 03 : **400 mots par liste, seuil 2, rappel négatif
0,770, précision négative 0,876** sur la validation.

### `labels.py` : les deux classes

`NEGATIVE = 0` et `POSITIVE = 1`. Écrire `labels == NEGATIVE` plutôt que `labels == 0` dit ce
que l'on cherche, et évite de se tromper de convention.

### `features/text.py` : des avis aux mots et aux nombres

| Élément | Rôle |
|---|---|
| `tokenize(text)` | découpe en mots : minuscules, suites de lettres et d'apostrophes (`"Don't BUY"` → `["don't", "buy"]`) |
| `build_vectorizer()` | crée le TF-IDF du projet : mots seuls + paires de mots, termes vus dans au moins 5 avis, `sublinear_tf` |

Le TF-IDF n'est encore utilisé par aucune commande : il est prêt pour les modèles de la phase 4.
`build_vectorizer()` renvoie un TF-IDF **vide** ; c'est à celui qui l'utilise d'appeler `fit` sur
le train, puis `transform` sur le reste.

### `models/keywords.py` : la règle mots-clés

| Élément | Rôle |
|---|---|
| `document_frequency(tokens)` | compte dans combien d'avis apparaît chaque mot (une fois par avis) |
| `KeywordClassifier(n_words, min_reviews, threshold)` | la règle, avec ses trois réglages (par défaut 400, 100, 2) |
| `.fit(texts, labels)` | apprend sur le train : garde les mots vus dans au moins `min_reviews` avis, calcule leur ratio (part des négatifs ÷ part des positifs), et les classe du plus négatif au plus positif (`ranking_`) |
| `.keyword_lists()` | les `n_words` premiers mots du classement (négatifs) et les `n_words` derniers (positifs) |
| `.negativity_score(texts)` | pour chaque avis : nombre de mots négatifs − nombre de mots positifs |
| `.predict(texts)` | label prédit : `NEGATIVE` si le score atteint le seuil, `POSITIVE` sinon |

- Même interface qu'un modèle scikit-learn (`fit` puis `predict`), sans en hériter : la classe
  reste simple et entièrement typée.
- Le classement est calculé **une seule fois** par `fit` ; changer `n_words` ou `threshold`
  ensuite ne demande pas de réapprendre. C'est ce qui rend l'essai de plusieurs tailles rapide.
- Les ratios sont arrondis à 2 décimales et les égalités départagées par ordre alphabétique,
  comme dans le notebook : les listes sont identiques d'une exécution à l'autre.
- Deux erreurs explicites : `NotFittedModelError` si on prédit avant `fit`, `KeywordListError`
  si l'on demande plus de mots qu'il n'y a de mots fréquents (les deux listes se chevaucheraient).

### `evaluation/metrics.py` : les métriques du projet

| Fonction | Rôle |
|---|---|
| `negative_metrics(labels, flagged)` | les 5 scores du projet : `neg_recall`, `neg_precision`, `neg_f1`, `pos_f1`, `accuracy` ; un avis « signalé » (`flagged`) est prédit négatif |
| `confusion_counts(labels, flagged)` | les 4 cases de la matrice de confusion : `negative_flagged`, `negative_missed`, `positive_flagged`, `positive_kept` |
| `threshold_table(score, labels)` | les scores obtenus pour chaque seuil entier, du plus petit au plus grand score |
| `best_threshold(table)` | le seuil au meilleur rappel parmi ceux dont la précision atteint `PRECISION_MIN` (0,85) ; lève `ThresholdNotFoundError` s'il n'y en a aucun |

Ces fonctions ne connaissent pas la règle mots-clés : elles serviront telles quelles pour les
modèles de la phase 4.

### `tracking.py` : la connexion à MLflow

`use_experiment(name)` pointe MLflow vers `mlflow.db` (à la racine du projet) et crée
l'expérience au besoin, avec ses fichiers joints dans `mlartifacts/`. Sans cet emplacement
explicite, MLflow rangerait les fichiers dans un dossier `mlruns/` créé là où l'on se trouve :
le notebook (lancé depuis `notebooks/`) et les commandes (lancées depuis la racine) ne les
mettraient pas au même endroit.

### `models/baseline.py` : la commande

| Élément | Rôle |
|---|---|
| `BaselineResult` | un essai à enregistrer : nom, réglages, scores, fichiers joints |
| `load_split(name)` | lit un jeu propre (`"train"`, `"validation"`) |
| `majority_baseline(train, val)` | la classe majoritaire du train, mesurée sur la validation |
| `keyword_baseline(train, val, n_words_grid, min_reviews)` | apprend la règle sur le train ; pour chaque taille de liste, cherche le meilleur seuil sur la validation ; garde la taille au meilleur rappel |
| `log_result(result)` | enregistre un essai dans MLflow (un *run*) |
| `main()` | enchaîne le tout et affiche les scores |

Une taille de liste qui ne peut pas atteindre la précision de 85 % est **écartée** (et non
bloquante) ; si aucune n'y parvient, la commande s'arrête avec `ThresholdNotFoundError`.

### `errors.py` : trois erreurs de plus

| Erreur | Quand |
|---|---|
| `ThresholdNotFoundError` | aucun seuil ne tient le plancher de précision |
| `NotFittedModelError` | un modèle est utilisé avant `fit` |
| `KeywordListError` | pas assez de mots fréquents pour deux listes distinctes |

Chacune fabrique elle-même son message à partir de quelques valeurs
(`ThresholdNotFoundError(0.85)` → « aucun seuil n'atteint une précision négative de 85% ») : le
texte de l'erreur est écrit à un seul endroit.

### Un avis, du début à la fin

Titre `"Junk"`, contenu `"Stopped working, I want a refund"`, label réel 0 (négatif).

| Étape | Résultat |
|---|---|
| texte lu (`full_text`) | `"Junk Stopped working, I want a refund"` |
| mots (`tokenize`) | `junk`, `stopped`, `working`, `i`, `want`, `a`, `refund` |
| mots-clés trouvés | négatifs : `junk`, `stopped`, `refund` ; positifs : aucun |
| score (`negativity_score`) | 3 − 0 = **3** |
| décision (`predict`) | 3 ≥ 2 (le seuil) → **signalé**, label prédit 0 : bonne réponse |

**Et le seuil 2, d'où vient-il ?** Avec 400 mots par liste, `threshold_table` donne sur la
validation : seuil 1 → rappel 84,8 %, précision 83,3 % (sous le plancher, refusé) ; seuil 2 →
rappel 77,0 %, précision 87,6 % (accepté). `best_threshold` garde donc 2.

### Les tests

| Fichier | Ce qu'il vérifie |
|---|---|
| `features/test_text.py` | le découpage en mots ; la présence des paires (« not good ») ; l'oubli des termes trop rares ; **aucune fuite** : un mot vu seulement en validation n'entre pas dans le vocabulaire |
| `models/test_keywords.py` | le classement sur un mini-train calculé à la main ; les égalités par ordre alphabétique ; le filtre des mots rares ; **aucune fuite** : les listes ne contiennent que des mots du train ; le score compte chaque occurrence ; les deux erreurs (`NotFittedModelError`, `KeywordListError`) |
| `evaluation/test_metrics.py` | les scores sur 4 avis calculés à la main ; les cases de la matrice de confusion ; le choix du seuil (meilleur rappel, plancher respecté, plus petit seuil en cas d'égalité) ; l'erreur quand aucun seuil ne convient |
| `models/test_baseline.py` | la classe majoritaire ; le choix de la taille et du seuil ; l'arrêt si aucune taille ne tient le plancher ; la commande complète, avec MLflow dans un dossier temporaire |

Un avertissement interne de MLflow (option dépréciée de SQLAlchemy 2.1) est ignoré dans la
configuration de pytest, et **seulement celui-là** : tout autre avertissement fait échouer les tests.

### Notions Python rencontrées

| Notion | En une phrase |
|---|---|
| `Counter` | un dictionnaire qui compte : `Counter(["a", "b", "a"])` donne `{"a": 2, "b": 1}` |
| `Self` | le type de retour « la même classe », utilisé par `fit` qui renvoie le modèle lui-même |
| attribut en `_` final (`ranking_`) | convention scikit-learn : un attribut qui n'existe qu'après `fit` |
| `sort_values(kind="stable")` | un tri qui garde l'ordre d'origine des égalités |
| `try` / `except … continue` | intercepter une erreur **attendue** pour passer au cas suivant, jamais pour la cacher |
| `field(default_factory=dict)` | valeur par défaut d'un attribut de dataclass : un dictionnaire neuf pour chaque objet |
| `with mlflow.start_run():` | ouvre un run, et le ferme même en cas d'erreur (un *gestionnaire de contexte*) |
| `monkeypatch.setattr(module, "CONST", …)` | remplace une constante le temps d'un test (ici, une grille plus petite) |
