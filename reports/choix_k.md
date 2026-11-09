# Application de la règle de choix de k

Rapport généré par `scripts/choisir_k.py`. Règle appliquée telle qu'écrite dans `docs/CHOIX.md` (poussée avant tout calcul). **Aucun avis chargé.**

## 1. Valeurs exactes (toutes les décimales)

Silhouette (échantillon commun de 8 000), Calinski-Harabasz et Davies-Bouldin recalculés à partir des étiquettes enregistrées (écart relatif maximal avec les valeurs publiées, arrondies à 6 chiffres : 3.8e-06). ARI bootstrap moyen et Jaccard le plus faible : valeurs publiées (6 chiffres significatifs).

| k | plus petit segment (%) | ARI bootstrap moyen | Jaccard le plus faible | silhouette | Calinski-Harabasz | Davies-Bouldin |
|---|---|---|---|---|---|---|
| 2 | 45.7125221819304 | 0.975027 | 0.986321 | 0.15655800896250785 | 12207.1090565837 | 2.064145341811101 |
| 3 | 2.979708355836741 | 0.913687 | 0.79018 | 0.1799126349971677 | 12648.008248987517 | 1.5631156533140664 |
| 4 | 2.979708355836741 | 0.802368 | 0.685031 | 0.20074506185064514 | 13113.287099680467 | 1.431280656086902 |
| 5 | 2.979708355836741 | 0.907439 | 0.899913 | 0.19962757598185818 | 13534.672087503293 | 1.3534269318138645 |
| 6 | 2.979708355836741 | 0.977801 | 0.975882 | 0.19761907474600082 | 13700.353701616363 | 1.3563181801644149 |
| 7 | 2.979708355836741 | 0.978737 | 0.973859 | 0.19625294071901445 | 13514.193607837577 | 1.2810351799095152 |
| 8 | 2.979708355836741 | 0.943056 | 0.912111 | 0.1802320303978917 | 12742.57706308569 | 1.320133434718827 |

## 2. Admissibilité

(a) plus petit segment ≥ 2 % ; (b) ARI bootstrap moyen ≥ 0,80 ; (c) Jaccard moyen de chaque segment ≥ 0,60.

| k | (a) | (b) | (c) | admissible |
|---|---|---|---|---|
| 2 | oui | oui | oui | oui |
| 3 | oui | oui | oui | oui |
| 4 | oui | oui | oui | oui |
| 5 | oui | oui | oui | oui |
| 6 | oui | oui | oui | oui |
| 7 | oui | oui | oui | oui |
| 8 | oui | oui | oui | oui |

## 3. Rangs parmi les k admissibles (1 = meilleur)

Silhouette : la plus haute = 1 ; Calinski-Harabasz : le plus haut = 1 ; Davies-Bouldin : le plus bas = 1. La plus petite somme gagne ; égalité : le plus petit k.

| k | rang silhouette | rang Calinski-Harabasz | rang Davies-Bouldin | somme |
|---|---|---|---|---|
| 2 | 7 | 7 | 7 | 21 |
| 3 | 6 | 6 | 6 | 18 |
| 4 | 1 | 4 | 5 | 10 |
| 5 | 2 | 2 | 3 | 7 |
| 6 | 3 | 1 | 4 | 8 |
| 7 | 4 | 3 | 1 | 8 |
| 8 | 5 | 5 | 2 | 12 |

**k obtenu : 5** (règle 3 (somme des rangs parmi les admissibles)).

## 4. Les 50 ARI bootstrap pour k = 5

Moyenne recalculée : 0.9074394414761894 (publiée : 0.907439) ; minimum 0.3453 ; médiane 0.9817.

**Tirages sous 0,80 : 6 sur 50.**

| tranche d'ARI | tirages |
|---|---|
| < 0,40 | 4 |
| 0,40 – 0,60 | 2 |
| 0,60 – 0,80 | 0 |
| 0,80 – 0,90 | 0 |
| 0,90 – 0,95 | 2 |
| ≥ 0,95 | 42 |

ARI de chaque tirage (dans l'ordre) : 0.354, 0.989, 0.982, 0.988, 0.980, 0.986, 0.976, 0.987, 0.983, 0.992, 0.982, 0.971, 0.962, 0.983, 0.982, 0.981, 0.973, 0.960, 0.987, 0.940, 0.975, 0.987, 0.983, 0.985, 0.986, 0.978, 0.986, 0.983, 0.985, 0.982, 0.988, 0.996, 0.404, 0.374, 0.977, 0.968, 0.980, 0.978, 0.922, 0.389, 0.988, 0.968, 0.345, 0.985, 0.983, 0.443, 0.971, 0.985, 0.982, 0.980

## 5. La découpe « concurrente » (tirages sous 0,80)

Accord entre les 6 partitions concurrentes : ARI de 0.686 à 0.946.

Tirage le plus éloigné (n° 43, ARI 0.345) : répartition de chaque segment de référence (lignes, en %) dans les segments de la découpe concurrente (colonnes).

| référence \ concurrente | C0 | C1 | C2 | C3 | C4 |
|---|---|---|---|---|---|
| S0 | 57.3 | 42.7 | 0.0 | 0.0 | 0.0 |
| S1 | 40.5 | 0.2 | 59.2 | 0.1 | 0.0 |
| S2 | 15.1 | 53.5 | 30.1 | 1.3 | 0.0 |
| S3 | 0.0 | 0.1 | 1.2 | 98.7 | 0.0 |
| S4 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 |

Profil des segments de la découpe concurrente (médianes, unités d'origine) :

| segment | clients | Récence (j) | Fréquence | Montant (R$) | Part frais de port | Mensualités | Articles/commande | Délai livraison (j) | Écart date promise (j) | part du CA (%) | en retard (%) | plusieurs commandes (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C0 | 24851 (38.3 %) | 174.00 | 1.00 | 85.20 | 0.16 | 1.00 | 1.00 | 8.00 | -14.00 | 28.9 | 0.2 | 0.0 |
| C1 | 16669 (25.7 %) | 208.00 | 1.00 | 159.90 | 0.12 | 5.00 | 1.00 | 14.63 | -10.00 | 46.3 | 14.7 | 0.0 |
| C2 | 15397 (23.8 %) | 198.00 | 1.00 | 29.90 | 0.35 | 1.00 | 1.00 | 13.86 | -11.00 | 6.0 | 11.0 | 0.0 |
| C3 | 5957 (9.2 %) | 193.00 | 1.00 | 139.80 | 0.21 | 2.00 | 2.00 | 10.21 | -14.00 | 13.6 | 5.0 | 0.0 |
| C4 | 1931 (3.0 %) | 167.00 | 2.00 | 179.46 | 0.18 | 2.50 | 1.00 | 11.26 | -13.00 | 5.3 | 4.5 | 100.0 |

## 6. Profil des 5 segments retenus par la règle (médianes, unités d'origine)

Segments numérotés du plus grand au plus petit. Montants en R$.

| segment | clients | Récence (j) | Fréquence | Montant (R$) | Part frais de port | Mensualités | Articles/commande | Délai livraison (j) | Écart date promise (j) | part du CA (%) | en retard (%) | plusieurs commandes (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S0 | 26066 (40.2 %) | 201.00 | 1.00 | 129.90 | 0.12 | 3.00 | 1.00 | 9.21 | -14.00 | 57.0 | 0.0 | 0.0 |
| S1 | 20690 (31.9 %) | 199.00 | 1.00 | 35.00 | 0.29 | 1.00 | 1.00 | 9.86 | -14.00 | 8.9 | 0.7 | 0.0 |
| S2 | 10227 (15.8 %) | 158.00 | 1.00 | 98.90 | 0.18 | 2.00 | 1.00 | 24.22 | -1.00 | 15.4 | 40.7 | 0.0 |
| S3 | 5891 (9.1 %) | 194.00 | 1.00 | 139.00 | 0.21 | 2.00 | 2.00 | 10.16 | -14.00 | 13.5 | 3.0 | 0.0 |
| S4 | 1931 (3.0 %) | 167.00 | 2.00 | 179.46 | 0.18 | 2.50 | 1.00 | 11.26 | -13.00 | 5.3 | 4.5 | 100.0 |

**Ce rapport n'est pas un choix final** : le critère métier (règle 4) reste à juger, et rien n'est commité avant cela. Aucun avis n'a été chargé.
