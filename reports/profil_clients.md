# Profil client : résumé

Rapport généré par `scripts/construire_profil.py`. Une ligne par vrai client (`customer_unique_id`). Commandes livrées avec date de livraison, achetées du 2017-01-01 au 2018-06-30 ; Récence comptée à partir du 2018-07-01. Montants en R$. Aucune donnée d'avis utilisée.

## Effectifs

| mesure | valeur |
|---|---|
| commandes retenues | 83 696 |
| clients (profils) | 81 006 |
| apprentissage (80 %) | 64 805 |
| mis de côté (20 %) | 16 201 |
| clients en commun entre les deux groupes | 0 |
| valeurs manquantes dans les 8 variables | 0 |
| tirage | identique à l'empreinte enregistrée |

## Statistiques des 8 variables (apprentissage, 80 %)

| variable | min | Q1 | médiane | Q3 | 99e centile | max |
|---|---|---|---|---|---|---|
| Récence (jours) | 1.00 | 96.00 | 191.00 | 309.00 | 514.00 | 542.00 |
| Fréquence (commandes) | 1.00 | 1.00 | 1.00 | 1.00 | 2.00 | 10.00 |
| Montant (R$, prix des articles) | 0.85 | 47.80 | 89.90 | 154.90 | 999.90 | 13 440.00 |
| Part des frais de port | 0.00 | 0.12 | 0.18 | 0.27 | 0.59 | 0.96 |
| Mensualités moyennes | 1.00 | 1.00 | 2.00 | 4.00 | 10.00 | 24.00 |
| Articles par commande | 1.00 | 1.00 | 1.00 | 1.00 | 3.00 | 20.00 |
| Délai de livraison moyen (jours) | 0.53 | 7.09 | 10.96 | 16.42 | 47.14 | 209.63 |
| Écart moyen à la date promise (jours) | -147.00 | -17.00 | -13.00 | -8.00 | 20.00 | 188.00 |

## Comparaison des 80 % et des 20 %

Écart standardisé = |moyenne 80 % − moyenne 20 %| / écart-type sur tous les clients. En dessous de 0,1, la différence est négligeable.

| variable | médiane 80 % | médiane 20 % | moyenne 80 % | moyenne 20 % | écart standardisé |
|---|---|---|---|---|---|
| Récence (jours) | 191.00 | 191.00 | 208.91 | 208.30 | 0.005 |
| Fréquence (commandes) | 1.00 | 1.00 | 1.03 | 1.03 | 0.004 |
| Montant (R$, prix des articles) | 89.90 | 89.90 | 141.32 | 142.92 | 0.007 |
| Part des frais de port | 0.18 | 0.18 | 0.21 | 0.21 | 0.003 |
| Mensualités moyennes | 2.00 | 2.00 | 2.94 | 2.91 | 0.011 |
| Articles par commande | 1.00 | 1.00 | 1.14 | 1.14 | 0.003 |
| Délai de livraison moyen (jours) | 10.96 | 10.96 | 13.19 | 13.15 | 0.004 |
| Écart moyen à la date promise (jours) | -13.00 | -13.00 | -12.09 | -12.06 | 0.003 |

| mesure | 80 % | 20 % |
|---|---|---|
| clients à plusieurs commandes (%) | 2.98 | 2.98 |
| clients livrés en retard en moyenne (écart moyen > 0) (%) | 7.06 | 7.12 |

## Colonnes de description (jamais dans le clustering)

**État** (6 premiers, % des clients)

| État | 80 % | 20 % |
|---|---|---|
| SP | 41.1 | 41.4 |
| RJ | 13.0 | 12.9 |
| MG | 11.9 | 12.0 |
| RS | 5.6 | 5.7 |
| PR | 5.2 | 4.8 |
| SC | 3.7 | 3.9 |

**Moyen de paiement principal** (% des clients)

| moyen | 80 % | 20 % |
|---|---|---|
| credit_card | 75.7 | 75.1 |
| boleto | 20.0 | 20.7 |
| voucher | 3.2 | 3.1 |
| debit_card | 1.2 | 1.1 |

**Catégorie principale** (6 premières, % des clients)

| catégorie | 80 % | 20 % |
|---|---|---|
| bed_bath_table | 9.6 | 9.6 |
| health_beauty | 8.6 | 8.3 |
| sports_leisure | 7.9 | 7.9 |
| computers_accessories | 6.9 | 6.6 |
| furniture_decor | 6.4 | 6.4 |
| housewares | 5.6 | 5.5 |

Catégories distinctes : 74 (dont « inconnue » : 1.53 %).
