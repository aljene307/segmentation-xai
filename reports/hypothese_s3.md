# Hypothèse sur S3 : plusieurs vendeurs, plusieurs colis ?

Rapport généré par `scripts/analyser_s3.py`. **Description seulement** : rien ne change dans la segmentation. Clients d'apprentissage avec avis (80 %) ; avis des 20 % non lus. « Plusieurs vendeurs » = au moins une commande retenue du client comptait des articles de plusieurs vendeurs (donc, probablement, plusieurs colis).

| groupe | clients avec avis | satisfaits (%) | note moyenne | note = 1 (%) |
|---|---|---|---|---|
| S3 — au moins une commande à plusieurs vendeurs | 738 | 39.2 | 2.83 | 36.7 |
| S3 — un seul vendeur par commande | 5092 | 67.2 | 3.76 | 18.6 |
| tous les autres segments — au moins une commande à plusieurs vendeurs | 101 | 53.5 | 3.63 | 9.9 |
| tous les autres segments — un seul vendeur par commande | 58443 | 79.5 | 4.18 | 8.8 |

| comparaison | écart de satisfaits (points) | intervalle de confiance à 95 % |
|---|---|---|
| S3 : plusieurs vendeurs moins un seul | -28.0 | [-31.8 ; -24.3] |
| tous les autres segments : plusieurs vendeurs moins un seul | -26.0 | [-35.8 ; -16.3] |

Part des clients de S3 concernés par plusieurs vendeurs : 12.7 %.

**Lecture** : l'écart est net (au moins 10 points, intervalle entièrement sous 0). C'est une piste qui soutient l'hypothèse, sans la prouver : la comparaison est descriptive, et d'autres différences entre ces clients peuvent jouer.
