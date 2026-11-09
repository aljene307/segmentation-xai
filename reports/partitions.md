# Étape 5 : partitions, indices internes et stabilité

Rapport généré par `scripts/construire_partitions.py`. Clients d'apprentissage (64 805) seulement ; aucun avis chargé. **La règle de choix de k n'est pas encore appliquée.** Paramètres fixés avant le calcul (voir `docs/CHOIX.md`).

Mémoire libre au démarrage : 7.14 Go (minimum exigé 2.0 Go). Pic de mémoire du calcul : 1.50 Go.

## 1. K-Means sur les 8 variables (méthode de référence)

Indices internes : R², silhouette (échantillon fixe de 8 000 clients), Calinski-Harabasz, Davies-Bouldin. Stabilité : 50 tirages bootstrap.

| k | plus petit segment (%) | R² | silhouette ↑ | Calinski-Harabasz ↑ | Davies-Bouldin ↓ | ARI bootstrap moyen | ARI bootstrap min | Jaccard moyen le plus faible |
|---|---|---|---|---|---|---|---|---|
| 2 | 45.71 | 0.159 | 0.157 | 12 207 | 2.064 | 0.975 | 0.931 | 0.986 |
| 3 | 2.98 | 0.281 | 0.180 | 12 648 | 1.563 | 0.914 | 0.722 | 0.790 |
| 4 | 2.98 | 0.378 | 0.201 | 13 113 | 1.431 | 0.802 | 0.304 | 0.685 |
| 5 | 2.98 | 0.455 | 0.200 | 13 535 | 1.353 | 0.907 | 0.345 | 0.900 |
| 6 | 2.98 | 0.514 | 0.198 | 13 700 | 1.356 | 0.978 | 0.960 | 0.976 |
| 7 | 2.98 | 0.556 | 0.196 | 13 514 | 1.281 | 0.979 | 0.962 | 0.974 |
| 8 | 2.98 | 0.579 | 0.180 | 12 743 | 1.320 | 0.943 | 0.836 | 0.912 |

**Jaccard moyen de chaque segment** (segments numérotés du plus grand au plus petit) :

| k | Jaccard par segment |
|---|---|
| 2 | 0.99 ; 0.99 |
| 3 | 0.95 ; 0.96 ; 0.79 |
| 4 | 0.86 ; 0.90 ; 0.69 ; 1.00 |
| 5 | 0.92 ; 0.93 ; 0.90 ; 0.99 ; 1.00 |
| 6 | 0.98 ; 0.98 ; 0.98 ; 0.98 ; 1.00 ; 1.00 |
| 7 | 0.98 ; 0.98 ; 0.98 ; 0.98 ; 0.97 ; 1.00 ; 1.00 |
| 8 | 0.91 ; 0.93 ; 0.98 ; 0.97 ; 0.97 ; 1.00 ; 0.94 ; 1.00 |

**Taille des segments (% des clients)** :

| k | tailles |
|---|---|
| 2 | 54.3 ; 45.7 |
| 3 | 53.8 ; 43.2 ; 3.0 |
| 4 | 49.1 ; 38.5 ; 9.4 ; 3.0 |
| 5 | 40.2 ; 31.9 ; 15.8 ; 9.1 ; 3.0 |
| 6 | 34.1 ; 20.9 ; 19.9 ; 13.3 ; 8.9 ; 3.0 |
| 7 | 24.9 ; 18.0 ; 17.4 ; 15.9 ; 12.0 ; 8.9 ; 3.0 |
| 8 | 17.3 ; 16.7 ; 16.3 ; 16.0 ; 14.7 ; 8.9 ; 7.1 ; 3.0 |

## 2. Comparaison des méthodes (indices dans le même espace : les 8 variables préparées)

Silhouette sur l'échantillon commun (8 000), ou sur les 6 000 de la CAH pour la CAH de Ward. ARI avec K-Means = accord avec la méthode de référence au même k.

**Mise en garde** : l'indice de Calinski-Harabasz augmente avec le nombre de clients. La valeur de la CAH de Ward, calculée sur 6 000 clients, n'est pas comparable aux valeurs calculées sur les 64 805 clients. Silhouette, Davies-Bouldin et R² restent comparables entre méthodes.

| méthode | k | clients | plus petit (%) | bruit (%) | R² | silhouette | Calinski-Harabasz | Davies-Bouldin | cophénétique | ARI avec K-Means |
|---|---|---|---|---|---|---|---|---|---|---|
| CAH de Ward (8 variables, 6 000) | 2 | 6 000 | 3.17 | 0.0 | 0.135 | 0.497 | 938 | 0.787 | 0.531 | -0.005 |
| CAH de Ward (8 variables, 6 000) | 3 | 6 000 | 3.17 | 0.0 | 0.250 | 0.186 | 999 | 1.848 | 0.531 | 0.247 |
| CAH de Ward (8 variables, 6 000) | 4 | 6 000 | 3.17 | 0.0 | 0.354 | 0.200 | 1 095 | 1.537 | 0.531 | 0.350 |
| CAH de Ward (8 variables, 6 000) | 5 | 6 000 | 3.17 | 0.0 | 0.413 | 0.183 | 1 052 | 1.371 | 0.531 | 0.315 |
| CAH de Ward (8 variables, 6 000) | 6 | 6 000 | 3.17 | 0.0 | 0.464 | 0.148 | 1 038 | 1.453 | 0.531 | 0.455 |
| CAH de Ward (8 variables, 6 000) | 7 | 6 000 | 3.17 | 0.0 | 0.500 | 0.129 | 1 000 | 1.525 | 0.531 | 0.446 |
| CAH de Ward (8 variables, 6 000) | 8 | 6 000 | 3.17 | 0.0 | 0.528 | 0.130 | 957 | 1.558 | 0.531 | 0.420 |
| Mixte F1–F5 | 2 | 64 805 | 2.98 | 0.0 | 0.128 | 0.498 | 9 505 | 0.794 | 0.506 | -0.005 |
| Mixte F1–F5 | 3 | 64 805 | 2.98 | 0.0 | 0.281 | 0.180 | 12 646 | 1.565 | 0.506 | 0.971 |
| Mixte F1–F5 | 4 | 64 805 | 2.98 | 0.0 | 0.378 | 0.200 | 13 110 | 1.433 | 0.506 | 0.973 |
| Mixte F1–F5 | 5 | 64 805 | 2.98 | 0.0 | 0.455 | 0.200 | 13 520 | 1.355 | 0.506 | 0.958 |
| Mixte F1–F5 | 6 | 64 805 | 2.98 | 0.0 | 0.507 | 0.186 | 13 326 | 1.395 | 0.506 | 0.549 |
| Mixte F1–F5 | 7 | 64 805 | 2.98 | 0.0 | 0.548 | 0.186 | 13 068 | 1.311 | 0.506 | 0.735 |
| Mixte F1–F5 | 8 | 64 805 | 2.98 | 0.0 | 0.570 | 0.168 | 12 251 | 1.366 | 0.506 | 0.657 |
| Mixte F1–F4 (sensibilité) | 2 | 64 805 | 45.35 | 0.0 | 0.159 | 0.156 | 12 206 | 2.062 | 0.458 | 0.982 |
| Mixte F1–F4 (sensibilité) | 3 | 64 805 | 11.79 | 0.0 | 0.260 | 0.169 | 11 396 | 1.849 | 0.458 | 0.735 |
| Mixte F1–F4 (sensibilité) | 4 | 64 805 | 11.24 | 0.0 | 0.338 | 0.168 | 11 051 | 1.686 | 0.458 | 0.642 |
| Mixte F1–F4 (sensibilité) | 5 | 64 805 | 10.90 | 0.0 | 0.391 | 0.152 | 10 414 | 1.646 | 0.458 | 0.513 |
| Mixte F1–F4 (sensibilité) | 6 | 64 805 | 10.56 | 0.0 | 0.431 | 0.152 | 9 812 | 1.559 | 0.458 | 0.516 |
| Mixte F1–F4 (sensibilité) | 7 | 64 805 | 10.32 | 0.0 | 0.450 | 0.132 | 8 822 | 1.632 | 0.458 | 0.515 |
| Mixte F1–F4 (sensibilité) | 8 | 64 805 | 4.17 | 0.0 | 0.507 | 0.147 | 9 502 | 1.567 | 0.458 | 0.430 |
| HDBSCAN (F1–F5) | 3 | 64 805 | 2.98 | 1.4 | 0.230 | 0.291 | 9 519 | 1.261 | — | 0.085 |

## 3. Contrôle de sensibilité : mixte à 5 axes contre mixte à 4 axes

ARI entre les deux partitions (1 = identiques). Description seulement : la décision de 5 axes ne change pas.

| k | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| ARI mixte 5 / mixte 4 | -0.006 | 0.720 | 0.637 | 0.509 | 0.624 | 0.600 | 0.498 |

## 4. Temps de calcul

| étape | secondes |
|---|---|
| K-Means de référence (20 initialisations, k = 2 à 8) | 8.8 |
| Bootstrap (50 tirages × 7 k × 10 initialisations) | 2 682.7 |
| CAH de Ward, 8 variables (6 000 clients) | 1.1 |
| Classification mixte F1–F5 (CAH 6 000 + consolidation) | 1.4 |
| Classification mixte F1–F4 (CAH 6 000 + consolidation) | 1.3 |
| HDBSCAN F1–F5 (64 805 clients) | 22.7 |

## 5. Ce que ce rapport ne fait pas

- Il n'applique pas la règle de choix de k (admissibilité, rangs) : étape suivante.
- Il ne lit pas les avis : les indices externes viennent après le choix de k.
