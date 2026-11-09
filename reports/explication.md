# Explicabilité des segments (module 5)

Rapport généré par `scripts/expliquer_segments.py`. Règles fixées et poussées avant le calcul (voir `docs/CHOIX.md`). Segments officiels (centre le plus proche). Aucun avis lu. Montants en R$.

## 1. Profils des segments (80 %)

Indice de profil = moyenne du segment / moyenne globale (au moins 1,20 : nettement au-dessus ; au plus 0,80 : nettement en dessous). **Écart à la date promise : différence en jours** (moyenne du segment − moyenne globale).

| segment | clients | part du CA | Récence | Nombre de commandes | Montant | Part des frais de port | Mensualités moyennes | Articles par commande | Délai de livraison moyen | Écart à la date promise |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 Gros achats en plusieurs fois | 26088 (40,3 %) | 57,0 % | 1,03 | 0,97 | 1,42 | 0,59 | 1,32 | 0,88 | 0,75 | -3,2 j |
| S1 Petits achats, livraison chère | 20698 (31,9 %) | 8,9 % | 1,03 | 0,97 | 0,28 | 1,53 | 0,52 | 0,88 | 0,81 | -2,2 j |
| S2 Livraison lente ou en retard | 10197 (15,7 %) | 15,3 % | 0,89 | 0,97 | 0,97 | 0,92 | 0,99 | 0,89 | 2,10 | 13,8 j |
| S3 Achats de plusieurs articles | 5891 (9,1 %) | 13,5 % | 0,99 | 0,97 | 1,48 | 1,11 | 1,21 | 2,13 | 0,88 | -1,8 j |
| S4 Clients qui recommandent | 1931 (3,0 %) | 5,3 % | 0,91 | 2,04 | 1,78 | 0,96 | 1,13 | 1,07 | 0,97 | -0,7 j |

Médianes (unités d'origine) :

| segment | Récence | Nombre de commandes | Montant | Part des frais de port | Mensualités moyennes | Articles par commande | Délai de livraison moyen | Écart à la date promise |
|---|---|---|---|---|---|---|---|---|
| S0 | 201,0 jours | 1,0 | 129,90 R$ | 0,12 | 3,0 | 1,0 | 9,2 jours | -14,0 jours |
| S1 | 199,0 jours | 1,0 | 35,00 R$ | 0,29 | 1,0 | 1,0 | 9,9 jours | -14,0 jours |
| S2 | 158,0 jours | 1,0 | 98,90 R$ | 0,18 | 2,0 | 1,0 | 24,2 jours | -1,0 jours |
| S3 | 194,0 jours | 1,0 | 139,00 R$ | 0,21 | 2,0 | 2,0 | 10,2 jours | -14,0 jours |
| S4 | 167,0 jours | 2,0 | 179,46 R$ | 0,18 | 2,5 | 1,0 | 11,3 jours | -13,0 jours |
| moyenne globale | 208,9 jours | 1,0 | 141,32 R$ | 0,21 | 2,9 | 1,1 | 13,2 jours | -12,1 jours |

| segment | 3 États principaux | paiement principal | 3 catégories principales |
|---|---|---|---|
| S0 | SP (46 %), MG (13 %), RJ (12 %) | credit_card (83 %) | bed_bath_table (10 %), health_beauty (9 %), watches_gifts (8 %) |
| S1 | SP (43 %), MG (12 %), RJ (11 %) | credit_card (67 %) | telephony (9 %), health_beauty (8 %), sports_leisure (8 %) |
| S2 | SP (24 %), RJ (19 %), MG (10 %) | credit_card (74 %) | bed_bath_table (11 %), health_beauty (8 %), sports_leisure (8 %) |
| S3 | SP (42 %), RJ (13 %), MG (12 %) | credit_card (76 %) | bed_bath_table (14 %), furniture_decor (13 %), computers_accessories (8 %) |
| S4 | SP (43 %), RJ (14 %), MG (12 %) | credit_card (77 %) | bed_bath_table (16 %), sports_leisure (11 %), furniture_decor (9 %) |

## 2. Arbre de décision de substitution

Variables en unités d'origine ; au moins 649 clients par feuille ; graine 42. Fidélité = part des clients pour lesquels l'arbre donne le segment officiel.

| profondeur | fidélité 80 % | fidélité 20 % | feuilles |
|---|---|---|---|
| 3 | 83,79 % | 83,93 % | 8 |
| 4 | 87,42 % | 87,75 % | 13 |

**Règle** : profondeur 3 si sa fidélité sur les 80 % atteint 90 % ; sinon 4 si elle gagne au moins 3 points ; sinon 3. **Profondeur retenue : 4.**

Fidélité par segment et confusions (lignes : segment officiel ; colonnes : segment donné par l'arbre ; en % de la ligne) :

**80 %**

| officiel \ arbre | S0 | S1 | S2 | S3 | S4 |
|---|---|---|---|---|---|
| S0 | 94,0 % | 4,6 % | 1,4 % | 0,0 % | 0,0 % |
| S1 | 12,2 % | 86,1 % | 1,1 % | 0,6 % | 0,0 % |
| S2 | 20,1 % | 8,6 % | 69,8 % | 1,4 % | 0,0 % |
| S3 | 0,0 % | 0,0 % | 1,3 % | 98,7 % | 0,0 % |
| S4 | 1,6 % | 8,3 % | 9,7 % | 8,7 % | 71,7 % |

**20 %**

| officiel \ arbre | S0 | S1 | S2 | S3 | S4 |
|---|---|---|---|---|---|
| S0 | 94,4 % | 4,3 % | 1,3 % | 0,0 % | 0,0 % |
| S1 | 12,1 % | 86,5 % | 0,9 % | 0,5 % | 0,0 % |
| S2 | 20,1 % | 8,8 % | 69,8 % | 1,3 % | 0,0 % |
| S3 | 0,0 % | 0,1 % | 0,8 % | 99,1 % | 0,0 % |
| S4 | 2,1 % | 8,1 % | 9,7 % | 7,7 % | 72,5 % |

**À lire avec l'arbre (hors de l'arbre)** : S4 « Clients qui recommandent » est exactement l'ensemble des clients à au moins 2 commandes : la règle « le client a au moins 2 commandes » le retrouve à 100,0 % (80 %). L'arbre ne le retrouve qu'à 71,7 %, car il cherche la meilleure fidélité globale et ne teste le nombre de commandes qu'au quatrième niveau d'une seule branche.

### Règles en phrases

1. Si le montant est au plus de 66,99 R$, l'écart à la date promise est au plus de -3,8 jours, le nombre moyen d'articles par commande est au plus de 1,8 et le nombre moyen de mensualités est au plus de 4,2, alors le client est le plus souvent dans S1 « Petits achats, livraison chère » (90 % des 19 417 clients de cette règle).
2. Si le montant est au plus de 66,99 R$, l'écart à la date promise est au plus de -3,8 jours, le nombre moyen d'articles par commande est au plus de 1,8 et le nombre moyen de mensualités est supérieur à 4,2, alors le client est le plus souvent dans S0 « Gros achats en plusieurs fois » (55 % des 1 707 clients de cette règle).
3. Si le montant est au plus de 66,99 R$, l'écart à la date promise est au plus de -3,8 jours et le nombre moyen d'articles par commande est supérieur à 1,8, alors le client est le plus souvent dans S3 « Achats de plusieurs articles » (88 % des 1 074 clients de cette règle).
4. Si le montant est au plus de 24,98 R$ et l'écart à la date promise est supérieur à -3,8 jours, alors le client est le plus souvent dans S1 « Petits achats, livraison chère » (63 % des 655 clients de cette règle).
5. Si le montant est entre 24,98 R$ et 66,99 R$ et l'écart à la date promise est entre -3,8 jours et -0,5 jours, alors le client est le plus souvent dans S2 « Livraison lente ou en retard » (67 % des 736 clients de cette règle).
6. Si le montant est entre 24,98 R$ et 66,99 R$ et l'écart à la date promise est supérieur à -0,5 jours, alors le client est le plus souvent dans S2 « Livraison lente ou en retard » (96 % des 1 506 clients de cette règle).
7. Si le montant est supérieur à 66,99 R$, le nombre moyen d'articles par commande est au plus de 1,9, l'écart à la date promise est au plus de -6,2 jours et le client a au plus 1 commande, alors le client est le plus souvent dans S0 « Gros achats en plusieurs fois » (86 % des 26 464 clients de cette règle).
8. Si le montant est supérieur à 66,99 R$, le nombre moyen d'articles par commande est au plus de 1,9, l'écart à la date promise est au plus de -6,2 jours et le client a au moins 2 commandes, alors le client est le plus souvent dans S4 « Clients qui recommandent » (100 % des 1 385 clients de cette règle).
9. Si le montant est supérieur à 66,99 R$, le nombre moyen d'articles par commande est au plus de 1,9, l'écart à la date promise est supérieur à -6,2 jours et le délai de livraison moyen est au plus de 13,3 jours, alors le client est le plus souvent dans S0 « Gros achats en plusieurs fois » (81 % des 955 clients de cette règle).
10. Si le montant est supérieur à 66,99 R$, le nombre moyen d'articles par commande est au plus de 1,9, l'écart à la date promise est supérieur à -6,2 jours et le délai de livraison moyen est supérieur à 13,3 jours, alors le client est le plus souvent dans S2 « Livraison lente ou en retard » (91 % des 5 725 clients de cette règle).
11. Si le montant est entre 66,99 R$ et 292,93 R$, le nombre moyen d'articles par commande est supérieur à 1,9 et le délai de livraison moyen est au plus de 21,1 jours, alors le client est le plus souvent dans S3 « Achats de plusieurs articles » (98 % des 3 523 clients de cette règle).
12. Si le montant est supérieur à 292,93 R$, le nombre moyen d'articles par commande est supérieur à 1,9 et le délai de livraison moyen est au plus de 21,1 jours, alors le client est le plus souvent dans S3 « Achats de plusieurs articles » (92 % des 1 009 clients de cette règle).
13. Si le montant est supérieur à 66,99 R$, le nombre moyen d'articles par commande est supérieur à 1,9 et le délai de livraison moyen est supérieur à 21,1 jours, alors le client est le plus souvent dans S3 « Achats de plusieurs articles » (75 % des 649 clients de cette règle).

## 3. Clients atypiques et à la frontière

Atypique : distance au centre de son segment au-delà du 95e centile des clients d'apprentissage de ce segment. À la frontière : distance au centre de son segment ≥ 90 % de la distance au 2e centre.

| segment | seuil atypique (distance) | atypiques 80 % | atypiques 20 % | à la frontière 80 % | à la frontière 20 % |
|---|---|---|---|---|---|
| S0 | 2,974 | 5,0 % | 5,2 % | 13,5 % | 13,3 % |
| S1 | 3,040 | 5,0 % | 4,4 % | 14,6 % | 14,5 % |
| S2 | 3,430 | 5,0 % | 5,2 % | 17,1 % | 17,3 % |
| S3 | 3,890 | 5,0 % | 5,5 % | 5,0 % | 5,1 % |
| S4 | 3,788 | 5,0 % | 5,2 % | 0,1 % | 0,0 % |
| **tous** |  | 5,0 % | 4,9 % | 13,3 % | 13,2 % |

## 4. Deux clients expliqués (clients mis de côté, traités comme de nouveaux clients)

### Client A

- Segment : **S2 « Livraison lente ou en retard »** ; distance au centre 1,500 (seuil atypique 3,430) → **typique**.
- 2e segment le plus proche : S1 « Petits achats, livraison chère » (distance 2,688 ; rapport 0,56) → **pas à la frontière**.

**Ce qui explique son segment : les 3 variables qui l'éloignent le plus du client moyen**

| variable | part de l'écart | sens | valeur du client | moyenne globale | médiane du segment |
|---|---|---|---|---|---|
| Délai de livraison moyen | 44,3 % | au-dessus | 31,5 jours | 13,2 jours | 24,2 jours |
| Écart à la date promise | 26,2 % | au-dessus | 0,0 jours | -12,1 jours | -1,0 jours |
| Part des frais de port | 16,0 % | au-dessus | 0,33 | 0,21 | 0,18 |

**Ce qui explique s'il est atypique : les 3 variables qui l'éloignent le plus du centre de son segment**

| variable | part de l'écart | sens | valeur du client | moyenne globale | médiane du segment |
|---|---|---|---|---|---|
| Part des frais de port | 59,0 % | au-dessus | 0,33 | 0,21 | 0,18 |
| Mensualités moyennes | 33,1 % | en dessous | 1,0 | 2,9 | 2,0 |
| Délai de livraison moyen | 5,9 % | au-dessus | 31,5 jours | 13,2 jours | 24,2 jours |

### Client B

- Segment : **S2 « Livraison lente ou en retard »** ; distance au centre 3,444 (seuil atypique 3,430) → **atypique**.
- 2e segment le plus proche : S0 « Gros achats en plusieurs fois » (distance 5,584 ; rapport 0,62) → **pas à la frontière**.

**Ce qui explique son segment : les 3 variables qui l'éloignent le plus du client moyen**

| variable | part de l'écart | sens | valeur du client | moyenne globale | médiane du segment |
|---|---|---|---|---|---|
| Écart à la date promise | 66,4 % | au-dessus | 29,0 jours | -12,1 jours | -1,0 jours |
| Délai de livraison moyen | 24,9 % | au-dessus | 58,3 jours | 13,2 jours | 24,2 jours |
| Part des frais de port | 3,6 % | en dessous | 0,08 | 0,21 | 0,18 |

**Ce qui explique s'il est atypique : les 3 variables qui l'éloignent le plus du centre de son segment**

| variable | part de l'écart | sens | valeur du client | moyenne globale | médiane du segment |
|---|---|---|---|---|---|
| Écart à la date promise | 71,4 % | au-dessus | 29,0 jours | -12,1 jours | -1,0 jours |
| Délai de livraison moyen | 14,5 % | au-dessus | 58,3 jours | 13,2 jours | 24,2 jours |
| Part des frais de port | 6,6 % | en dessous | 0,08 | 0,21 | 0,18 |
