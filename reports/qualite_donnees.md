# Contrôle qualité des données brutes Olist

Rapport généré par `scripts/controle_qualite.py`. Comptes agrégés uniquement. Montants en réals brésiliens (R$).

## 1. Intégrité des fichiers

Source : https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce — licence CC BY-NC-SA 4.0.
Comparaison au manifeste `docs/donnees_manifeste.json` : identique.

## 2. Tables

| table | lignes | colonnes | doublons exacts | clé | doublons de clé |
|---|---|---|---|---|---|
| clients | 99 441 | 5 | 0 | customer_id | 0 |
| commandes | 99 441 | 8 | 0 | order_id | 0 |
| articles | 112 650 | 7 | 0 | order_id + order_item_id | 0 |
| paiements | 103 886 | 5 | 0 | order_id + payment_sequential | 0 |
| produits | 32 951 | 9 | 0 | product_id | 0 |
| vendeurs | 3 095 | 4 | 0 | seller_id | 0 |
| geolocalisation | 1 000 163 | 5 | 261 831 | — | — |
| traduction_categories | 71 | 2 | 0 | product_category_name | 0 |
| avis (à part) | 99 224 | 7 | 0 | review_id + order_id | 0 |

## 3. Valeurs manquantes

**commandes**

| colonne | manquants | % |
|---|---|---|
| order_approved_at | 160 | 0.16 |
| order_delivered_carrier_date | 1 783 | 1.79 |
| order_delivered_customer_date | 2 965 | 2.98 |

**produits**

| colonne | manquants | % |
|---|---|---|
| product_category_name | 610 | 1.85 |
| product_name_lenght | 610 | 1.85 |
| product_description_lenght | 610 | 1.85 |
| product_photos_qty | 610 | 1.85 |
| product_weight_g | 2 | 0.01 |
| product_length_cm | 2 | 0.01 |
| product_height_cm | 2 | 0.01 |
| product_width_cm | 2 | 0.01 |

**avis (à part)**

| colonne | manquants | % |
|---|---|---|
| review_comment_title | 87 656 | 88.34 |
| review_comment_message | 58 247 | 58.70 |

Aucune valeur manquante : clients, articles, paiements, vendeurs, geolocalisation, traduction_categories.

## 4. Clés de jointure

| contrôle | nombre |
|---|---|
| commandes.customer_id absents de clients | 0 |
| clients.customer_id sans commande | 0 |
| customer_id présents dans plusieurs commandes | 0 |
| articles.order_id absents de commandes | 0 |
| commandes sans article | 775 |
| articles.product_id absents de produits | 0 |
| articles.seller_id absents de vendeurs | 0 |
| paiements.order_id absents de commandes | 0 |
| commandes sans paiement | 1 |

## 5. Statuts de commande

| statut | commandes | % |
|---|---|---|
| delivered | 96 478 | 97.02 |
| shipped | 1 107 | 1.11 |
| canceled | 625 | 0.63 |
| unavailable | 609 | 0.61 |
| invoiced | 314 | 0.32 |
| processing | 301 | 0.30 |
| created | 5 | 0.01 |
| approved | 2 | 0.00 |

## 6. Chronologie des commandes

Achats du 2016-09-04 au 2018-10-17.

| contrôle | nombre |
|---|---|
| validation avant l achat | 0 |
| remise au transporteur avant l achat | 166 |
| livraison avant l achat | 0 |
| livraison avant remise au transporteur | 23 |
| livrées sans date de livraison | 8 |
| non livrées avec date de livraison | 6 |
| livrées en retard | 6 534 |
| livrées | 96 478 |

## 7. Montants (R$)

| contrôle | valeur |
|---|---|
| prix nul ou négatif | 0 |
| frais de port négatifs | 0 |
| frais de port nuls | 383 |
| paiement nul ou négatif | 9 |
| nombre de mensualités égal à 0 | 2 |
| commandes comparées | 98 665 |
| commandes avec écart paiements articles > 0,01 R$ | 378 |
| écart médian quand écart (R$) | 3.85 |

| variable (R$) | min | médiane | moyenne | max |
|---|---|---|---|---|
| price | 0.85 | 74.99 | 120.65 | 6 735.00 |
| freight_value | 0.00 | 16.26 | 19.99 | 409.68 |

| moyen de paiement | lignes |
|---|---|
| credit_card | 76 795 |
| boleto | 19 784 |
| voucher | 5 775 |
| debit_card | 1 529 |
| not_defined | 3 |

## 8. Clients : `customer_id` contre `customer_unique_id`

| mesure | valeur |
|---|---|
| customer_id distincts | 99 441 |
| customer_unique_id distincts (vrais clients) | 96 096 |
| clients avec 1 seule commande | 93 099 |
| part des clients avec 1 seule commande (%) | 96.88 |
| nombre maximal de commandes d'un client | 17 |

| commandes par client | clients |
|---|---|
| 1 | 93 099 |
| 2 | 2 745 |
| 3 | 203 |
| 4 | 30 |
| 5 | 8 |
| 6 | 6 |
| 7 | 3 |
| 9 | 1 |
| 17 | 1 |

## 9. Produits

| mesure | valeur |
|---|---|
| catégories distinctes | 73 |
| produits sans catégorie | 610 |
| catégories sans traduction anglaise | 2 |

Catégories sans traduction : pc_gamer, portateis_cozinha_e_preparadores_de_alimentos.

## 10. Avis (table tenue à l'écart, évaluation externe seulement)

| mesure | valeur |
|---|---|
| avis | 99 224 |
| review id distincts | 98 410 |
| review id sur plusieurs commandes | 789 |
| commandes avec avis | 98 673 |
| commandes avec plusieurs avis | 547 |
| commandes sans avis | 768 |
| avis orphelins | 0 |

| review_score | avis | % |
|---|---|---|
| 1 | 11 424 | 11.51 |
| 2 | 3 151 | 3.18 |
| 3 | 8 179 | 8.24 |
| 4 | 19 142 | 19.29 |
| 5 | 57 328 | 57.78 |

## 11. Mémoire

Pic de mémoire du contrôle (toutes tables chargées) : 330 Mo.
