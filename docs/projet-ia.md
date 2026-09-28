# Suivi du projet IA / data : ReviewPilot — classification de sentiment

- **Type** : ML (classification de texte binaire)
- **Phase en cours** : 2 — données
- **Dernière mise à jour** : 2026-09-28

## Déjà fait avant le démarrage du suivi
- **Données** : échantillon reproductible d'Amazon Polarity (50 000 avis train, 10 000 avis test), généré par `uv run python -m review_pilot.dataset` ; source, licence et colonnes dans [data/README.md](../data/README.md).
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
- **Baseline à battre** : règle mots-clés (compte les mots positifs et négatifs repérés dans l'EDA) (score : mesuré en phase 3). Contrôle minimal : classe majoritaire (~50 % d'accuracy).
- **Contraintes** : modèle explicable (savoir quels mots ont fait signaler un avis) ; entraînement en local (RTX 3080 10 Go, pas de cloud ni d'API payante) ; traitement par lots, sans contrainte de temps réel. Donnée personnelle repérée (une adresse postale) : retirée au nettoyage.
- **Hors périmètre de ce passage** : RAG et agent (passage suivant). Le fine-tuning d'un modèle de langage reste possible en phase 4 si nécessaire pour atteindre le seuil.
- **Risques connus** : les avis à 3★ (mitigés) sont absents des données alors qu'ils existent en conditions réelles ; données Amazon anglophones d'avant 2013 ; pas d'identifiant ni de catégorie de produit.

## Avancement
| Phase | Statut | Validée le | Livrables |
|---|---|---|---|
| 1. Besoin | validée | 2026-09-28 | cadre ci-dessus |
| 2. Données (+ split test) | en cours | | |
| 3. Features + baseline | à faire | | |
| 4. Modélisation | à faire | | |
| 5. Évaluation | à faire | | |
| 6. Explicabilité (SHAP / analyse d'erreurs) | à faire | | |
| Go / no-go | à décider | | |
| 7. Industrialisation | à faire | | |

## Jeu de test
- **Découpage** : … (aléatoire / temporel / par groupe), fichier : …
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
