# Suivi du projet IA / data : ReviewPilot — classification de sentiment

- **Type** : ML (classification de texte binaire)
- **Phase en cours** : 4 — modélisation
- **Dernière mise à jour** : 2026-09-29

## Déjà fait avant le démarrage du suivi
- **Données** : échantillon reproductible d'Amazon Polarity (50 000 avis train, 10 000 avis test), généré par `uv run python -m review_pilot.data.download` ; source, licence et colonnes dans [data/README.md](../data/README.md).
- **EDA** : [notebooks/01_eda.ipynb](../notebooks/01_eda.ipynb) (commit `47c6b1e`). Conclusions principales : classes équilibrées (50,08 % / 49,92 %), le sentiment se lit dans les mots et non dans la forme du texte, 93 avis non anglais et du bruit de format à nettoyer.
- **Jeu de test** : le split test d'origine n'a servi qu'à vérifier sa structure et l'absence de fuite exacte avec le train ; il n'a jamais servi à évaluer un modèle.

## Cadre fixé en phase 1 (ne change pas sans accord explicite)
- **Besoin / décision à éclairer** : signaler au service client les avis négatifs à traiter, pour ne pas laisser passer de client mécontent.
- **Cible** : `label` (0 = négatif, 1 = positif), issue des étoiles données par le client : 1-2★ = négatif, 4-5★ = positif, 3★ exclus du dataset. Pas d'horizon temporel (le sentiment est prédit à partir du texte de l'avis, déjà écrit).
- **Coût des erreurs** : rater un avis négatif (client mécontent non traité) coûte plus cher qu'une fausse alerte (un avis positif relu pour rien).
- **Métrique principale** : **rappel de la classe négative** (part des avis négatifs réellement signalés), sous contrainte d'une **précision de la classe négative ≥ 85 %** (au plus ~15 % de fausses alertes parmi les signalements). Le seuil de décision du modèle est réglé sur la validation pour respecter cette contrainte.
  — pourquoi elle reflète le besoin : elle mesure directement la part de clients mécontents trouvés ; le plancher de précision empêche la solution triviale « tout signaler ».
- **Métriques secondaires** : accuracy et F1 par classe (contrôle global, cf. conclusion de l'EDA), matrice de confusion.
- **Seuil de succès** : sur le test (phase 5), **rappel négatif ≥ 90 %** avec **précision négative ≥ 85 %**, et nettement meilleur que la baseline mots-clés.
- **Baseline à battre** : règle mots-clés (400 mots négatifs et 400 positifs appris sur le train, seuil 2), **mesurée en phase 3 sur la validation : rappel négatif 77,0 %, précision négative 87,6 %, accuracy 83,0 %** (run MLflow `keywords`, expérience `phase-3-baseline`). Contrôle minimal : classe majoritaire (« négatif ») : rappel 100 %, précision 50,1 %, exclue par le plancher de précision.
- **Contraintes** : modèle explicable (savoir quels mots ont fait signaler un avis) ; entraînement en local (RTX 3080 10 Go, pas de cloud ni d'API payante) ; traitement par lots, sans contrainte de temps réel. Donnée personnelle repérée (une adresse postale) : retirée au nettoyage.
- **Mode de travail** : notebook d'abord. Chaque phase est d'abord faite dans `notebooks/NN_nom.ipynb` (structure du notebook d'EDA), validée, puis portée en code testé dans `src/` ; le notebook reste tel quel ensuite. Commit en fin de phase validée, après accord.
- **Hors périmètre de ce passage** : RAG et agent (passage suivant). Le fine-tuning d'un modèle de langage reste possible en phase 4 si nécessaire pour atteindre le seuil.
- **Risques connus** : les avis à 3★ (mitigés) sont absents des données alors qu'ils existent en conditions réelles ; données Amazon anglophones d'avant 2013 ; pas d'identifiant ni de catégorie de produit ; le filtre de langue écarte quelques avis anglais très courts (17 dans le train, dont 9 négatifs), qui ne seraient jamais signalés en production ; les mots appris (règle mots-clés, et sans doute le futur modèle) captent en partie le **thème** du produit (« box », « connect » côté négatif, « history », « king » côté positif), ce qui pourrait mal se généraliser à d'autres catégories de produits (non vérifiable : pas de catégorie dans les données).

## Avancement
| Phase | Statut | Validée le | Livrables |
|---|---|---|---|
| 1. Besoin | validée | 2026-09-28 | cadre ci-dessus |
| 2. Données (+ split test) | validée | 2026-09-29 | `notebooks/02_data_cleaning.ipynb` ; `src/review_pilot/data/` (download, clean, split, quality, build) + tests ; `data/processed/` ; `reports/data_quality.md` ; `docs/architecture.md` ; README « Démarrer, pas à pas » |
| 3. Features + baseline | validée | 2026-09-29 | `notebooks/03_features_baseline.ipynb` ; `reports/figures/03_*.png` ; `src/review_pilot/` (features/text, models/keywords, models/baseline, evaluation/metrics, tracking, labels) + tests ; runs MLflow `phase-3-baseline` ; `docs/code.md` phase 3 |
| 4. Modélisation | en cours | | |
| 5. Évaluation | à faire | | |
| 6. Explicabilité (SHAP / analyse d'erreurs) | à faire | | |
| Go / no-go | à décider | | |
| 7. Industrialisation | à faire | | |

## Jeu de test
- **Découpage** : split test d'origine d'Amazon Polarity (aléatoire, fait par les auteurs du dataset), nettoyé avec les mêmes règles que le train : 9 975 avis, fichier `data/processed/test.parquet`. Pas de découpage temporel (aucune date) ni par groupe (aucun identifiant de produit).
- **Validation** : 10 % du train, découpage stratifié, graine 42 : 4 989 avis, `data/processed/val.parquet` (train : 44 896 avis).
- **Utilisé en évaluation finale le** : jamais

## Itérations (boucle 3 → 6)
| Date | Retour en phase | Raison | Effet sur le score |
|---|---|---|---|

## Décisions
| Date | Décision | Pourquoi |
|---|---|---|
| 2026-09-28 | Usage : repérer les avis négatifs pour le service client | usage concret, qui donne un sens aux erreurs et prépare le RAG et l'agent |
| 2026-09-28 | Métrique principale : rappel négatif, sous contrainte de précision négative ≥ 85 % | rater un négatif coûte plus cher qu'une fausse alerte ; l'accuracy et le F1 (choix par défaut de l'EDA) deviennent secondaires |
| 2026-09-28 | Seuil : rappel négatif ≥ 90 % avec précision négative ≥ 85 % sur le test | exigeant mais jugé atteignable par un bon modèle fondé sur les mots (non vérifié) |
| 2026-09-28 | Baseline : règle mots-clés (classe majoritaire en contrôle) | la classe majoritaire (~50 %) est trop facile à battre pour prouver quelque chose |
| 2026-09-28 | Contraintes : explicable, local, par lots | besoin du service client + apprentissage ; RTX 3080 disponible |
| 2026-09-28 | RAG et agent hors périmètre de ce passage | un passage `/projet-ia` = un modèle, du besoin à l'industrialisation |
| 2026-09-29 | Ajout au cadre : mode de travail « notebook d'abord », commit en fin de phase validée après accord | demande explicite : comprendre et valider chaque phase dans un notebook avant le code de production |
| 2026-09-29 | Test : garder le split test d'origine ; validation : 10 % du train, stratifiée | aucune date ni identifiant de produit pour un autre découpage ; ~2 500 négatifs en validation suffisent pour mesurer le rappel à environ un point près |
| 2026-09-29 | Données personnelles : e-mails et téléphones **masqués** (`[EMAIL]`, `[PHONE]`) plutôt qu'avis supprimés | la donnée disparaît mais l'avis reste utile ; les motifs d'adresse postale ne trouvaient que des faux positifs |
| 2026-09-29 | Code de données dans le paquet `review_pilot/data/` (dataset.py devient data/download.py) | une seule commande de création des données : `uv run python -m review_pilot.data.build` |
| 2026-09-29 | Listes de mots-clés **calculées sur le train** (ratio de fréquences documentaires, mots vus dans ≥ 100 avis) ; taille (400) et seuil (2) choisis sur la validation | reproductible et sans fuite ; le choix sur la validation rend le score un peu optimiste, le test tranchera en phase 5 |
| 2026-09-29 | Features pour la phase 4 : TF-IDF mots + paires de mots (`min_df=5`, `sublinear_tf`), titre + contenu ; variables de forme (longueur, `?`, `!`) écartées | les négations (« not recommend ») comptent ; la forme ne fait varier la part de négatifs que de 10 à 18 points |
| 2026-09-29 | Validation croisée (5 plis sur le train) reportée en phase 4 | elle sert à comparer et régler des modèles ; la baseline n'a presque rien à régler |
| 2026-09-29 | MLflow en local : `mlflow.db` (SQLite) et `mlartifacts/`, jamais versionnés | journal des essais sans serveur ni cloud ; même emplacement pour les notebooks et les commandes |
