# Évaluation externe des segments (note d'avis)

> **À lire d'abord.** Les variables de délai (délai de livraison moyen, écart à la date promise) entrent dans le clustering, et un retard entraîne souvent une mauvaise note. Le segment **S2 « Livraison lente ou en retard »**, défini par ces variables, sera donc lié à la note **par construction** : un lien entre S2 et l'insatisfaction ne prouve pas que la segmentation « découvre » la satisfaction. Par ailleurs, avec une étiquette à deux classes et des segments de comportement, l'ARI et la NMI sont faibles par nature ; les taux par segment sont les plus parlants (écrit d'avance dans `docs/CHOIX.md`).

Rapport généré par `scripts/evaluer_externe.py`, après le choix de k = 5 (commité et poussé). Segment de chaque client = segment officiel (centre le plus proche de `models/segments.json`). Clients d'apprentissage (80 %) seulement ; **les avis des 20 % mis de côté n'ont pas été lus**. Note du client = moyenne des notes de ses commandes retenues (avis le plus récent par commande) ; « satisfait » si la note vaut au moins 4 ; clients sans avis exclus des indices.

## 1. Couverture

| mesure | valeur |
|---|---|
| clients d'apprentissage | 64 805 |
| clients avec au moins un avis | 64 374 |
| clients sans avis (exclus des indices) | 431 (0.67 %) |
| clients à plusieurs commandes notées | 1 904 |
| part de satisfaits (note ≥ 4) | 78.0 % |

## 2. Indices externes (segments retenus contre « satisfait »)

| indice | valeur |
|---|---|
| ARI | 0.0670 |
| NMI | 0.0393 |
| V-measure | 0.0393 |
| homogénéité | 0.0698 |
| complétude | 0.0274 |

- **Homogénéité** : à quel point chaque segment ne contient qu'une seule classe (satisfaits ou non).
- **Complétude** : à quel point chaque classe tient dans un seul segment.
- **V-measure** : moyenne harmonique des deux ; la NMI en est très proche ici.

## 3. Par segment

| segment | clients | avec avis | sans avis (%) | satisfaits (%) | note moyenne | note = 1 (%) |
|---|---|---|---|---|---|---|
| S0 Gros achats en plusieurs fois | 26 088 | 25 955 | 0.5 | 85.7 | 4.39 | 5.1 |
| S1 Petits achats, livraison chère | 20 698 | 20 601 | 0.5 | 84.0 | 4.35 | 5.1 |
| S2 Livraison lente ou en retard | 10 197 | 10 065 | 1.3 | 54.9 | 3.31 | 27.1 |
| S3 Achats de plusieurs articles | 5 891 | 5 830 | 1.0 | 63.7 | 3.64 | 20.9 |
| S4 Clients qui recommandent | 1 931 | 1 923 | 0.4 | 74.1 | 4.19 | 4.3 |
| **Tous les clients d'apprentissage** | 64 805 | 64 374 | 0.7 | 78.0 | 4.13 | 9.9 |

## 4. Le lien retard / note, mesuré directement

| clients avec avis | clients | satisfaits (%) | note moyenne |
|---|---|---|---|
| livrés en retard en moyenne (écart > 0) | 4 473 | 24.9 | 2.22 |
| livrés à l'heure ou en avance | 59 901 | 82.0 | 4.27 |

## 5. Comparaison des méthodes au même k (information, ne change aucune décision)

| méthode | clients avec avis | ARI | NMI | V-measure | homogénéité | complétude |
|---|---|---|---|---|---|---|
| K-Means 8 variables, segments officiels, k = 5 | 64 374 | 0.0670 | 0.0393 | 0.0393 | 0.0698 | 0.0274 |
| Mixte F1–F5, k = 5 | 64 374 | 0.0682 | 0.0406 | 0.0406 | 0.0720 | 0.0282 |
| Mixte F1–F4 (sensibilité), k = 5 | 64 374 | 0.0392 | 0.0358 | 0.0358 | 0.0708 | 0.0240 |
| CAH de Ward 8 variables (6 000), k = 5 | 5 963 | 0.0996 | 0.0475 | 0.0475 | 0.0758 | 0.0345 |
| HDBSCAN F1–F5 (3 groupes, bruit exclu) | 63 498 | 0.0655 | 0.0118 | 0.0118 | 0.0107 | 0.0131 |
