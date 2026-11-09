# Segments officiels : centre le plus proche

Rapport généré par `scripts/enregistrer_segments.py`. Le segment officiel d'un client d'apprentissage est le centre le plus proche de `models/segments.json`, comme pour un nouveau client dans l'API. Comparaison avec la partition K-Means de référence (celle sur laquelle k a été choisi).

**Clients qui changent de segment : 34 sur 64805 (0.0525 %).**

Transitions (lignes : segment K-Means ; colonnes : segment officiel) :

| K-Means \ officiel | S0 | S1 |
|---|---|---|
| S0 | 0 | 1 |
| S1 | 3 | 0 |
| S2 | 20 | 10 |

| segment | clients K-Means | clients officiels | part du CA K-Means (%) | part du CA officielle (%) |
|---|---|---|---|---|
| S0 Gros achats en plusieurs fois | 26066 | 26088 | 56.97 | 57.00 |
| S1 Petits achats, livraison chère | 20690 | 20698 | 8.94 | 8.94 |
| S2 Livraison lente ou en retard | 10227 | 10197 | 15.35 | 15.31 |
| S3 Achats de plusieurs articles | 5891 | 5891 | 13.45 | 13.45 |
| S4 Clients qui recommandent | 1931 | 1931 | 5.29 | 5.29 |

Médianes des 8 variables avec la partition officielle (unités d'origine, R$) :

| segment | recence_j | frequence | montant_rs | part_frais_port | mensualites_moy | articles_par_commande | delai_livraison_moy_j | ecart_prevision_moy_j |
|---|---|---|---|---|---|---|---|---|
| S0 | 201.00 | 1.00 | 129.90 | 0.12 | 3.00 | 1.00 | 9.21 | -14.00 |
| S1 | 199.00 | 1.00 | 35.00 | 0.29 | 1.00 | 1.00 | 9.87 | -14.00 |
| S2 | 158.00 | 1.00 | 98.90 | 0.18 | 2.00 | 1.00 | 24.25 | -1.00 |
| S3 | 194.00 | 1.00 | 139.00 | 0.21 | 2.00 | 2.00 | 10.16 | -14.00 |
| S4 | 167.00 | 2.00 | 179.46 | 0.18 | 2.50 | 1.00 | 11.26 | -13.00 |

Plus grand écart relatif entre les médianes K-Means et officielles : 0.098 %.
