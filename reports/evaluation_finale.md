# Évaluation finale sur les 20 % mis de côté (ouverte une seule fois)

Calculée le 2026-11-09T15:40:13, au commit `fb081cd`. Attentes et seuils écrits et poussés avant l'ouverture (`docs/CHOIX.md`). Rien n'a été modifié après l'ouverture.

**Attentes atteintes : 12 sur 12.**

| n° | mesure | 80 % (référence) | 20 % | attente | atteinte | statut |
|---|---|---|---|---|---|---|
| E1 | part de chaque segment (%) | 40,26 ; 31,94 ; 15,73 ; 9,09 ; 2,98 | 40,1 ; 32 ; 15,76 ; 9,15 ; 2,98 | écart ≤ 1,0 point par segment | **oui** | inédit |
| E2 | silhouette (8 000 clients) | 0,1997 | 0,2008 | écart ≤ 0,02 | **oui** | inédit |
| E3 | atypiques (%) : total ; par segment | 5 | 4,94 ; 5,17 ; 4,38 ; 5,17 ; 5,46 ; 5,18 | total entre 4,0 et 6,0 % ; chaque segment entre 3,0 et 7,0 % | **oui** | déjà observé |
| E4 | clients à la frontière (%) | 13,26 | 13,15 | écart ≤ 1,5 point | **oui** | déjà observé |
| E5 | fidélité de l'arbre (%) | 87,42 | 87,75 | au moins 85 % et écart ≤ 2 points | **oui** | déjà observé |
| E6 | clients sans avis (%) | 0,67 | 0,7 | au plus 1,5 % | **oui** | inédit |
| E7 | satisfaits, tous segments (%) | 78,01 | 78,24 | écart ≤ 2 points | **oui** | inédit |
| E8 | satisfaits par segment (%) | 85,71 ; 84,03 ; 54,91 ; 63,65 ; 74,05 | 85,83 ; 84,99 ; 54,21 ; 64,1 ; 72,82 | écart ≤ 3 points (S0 à S3), ≤ 5 points (S4) | **oui** | inédit |
| E9 | ordre des segments (du plus au moins satisfait) | S0 ; S1 ; S4 ; S3 ; S2 | S0 ; S1 ; S4 ; S3 ; S2 | S2 dernier, S3 avant-dernier ; S0 et S1 ≥ 80 % | **oui** | inédit |
| E10 | ARI ; NMI | 0,067 ; 0,0393 | 0,0694 ; 0,0421 | ARI entre 0,04 et 0,10 ; NMI entre 0,02 et 0,06 | **oui** | inédit |
| E11 | satisfaits à l'heure moins en retard (points) | 57,07 | 59,3 | au moins 40 points | **oui** | inédit |
| E12 | S3 : plusieurs vendeurs moins un seul (points) | -28,04 | -35,3 | au plus −10 points | **oui** | inédit |

## Détail par segment (20 %)

| segment | part (%) | clients avec avis | satisfaits (%) | atypiques (%) |
|---|---|---|---|---|
| S0 Gros achats en plusieurs fois | 40.10 | 6456 | 85.8 | 5.2 |
| S1 Petits achats, livraison chère | 32.00 | 5164 | 85.0 | 4.4 |
| S2 Livraison lente ou en retard | 15.76 | 2518 | 54.2 | 5.2 |
| S3 Achats de plusieurs articles | 9.15 | 1468 | 64.1 | 5.5 |
| S4 Clients qui recommandent | 2.98 | 482 | 72.8 | 5.2 |

Lien retard / note (20 %) : 82.4 % de satisfaits à l'heure contre 23.1 % en retard. Hypothèse S3 (20 %) : 181 clients à plusieurs vendeurs contre 1287 à un seul.
