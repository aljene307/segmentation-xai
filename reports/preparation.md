# Préparation des variables : avant / après

Rapport généré par `scripts/preparer.py`. Paramètres appris sur les 64 805 clients d'apprentissage (80 %) seulement, enregistrés dans `models/preparation.json`, puis réappliqués tels quels aux 16 201 clients mis de côté (20 %). Ordre : log → écrêtage → standardisation. Règles fixées avant tout segment (voir `docs/CHOIX.md`).

État : paramètres recalculés identiques au fichier enregistré.

## 1. Règle du log

`log(1 + x)` pour une variable positive et sans borne haute, si son asymétrie dépasse 1 et si le log la réduit.

| variable | asymétrie brute | asymétrie après log | log | raison |
|---|---|---|---|---|
| Récence (jours) | 0.47 | -1.35 | non | asymétrie ≤ 1 |
| Fréquence (commandes) | 9.16 | 6.48 | oui | positive, sans borne, asymétrique : log |
| Montant (R$) | 10.00 | 0.27 | oui | positive, sans borne, asymétrique : log |
| Part des frais de port | 1.08 | — | non | proportion bornée : hors de la règle |
| Mensualités moyennes | 1.59 | 0.79 | oui | positive, sans borne, asymétrique : log |
| Articles par commande | 7.49 | 3.95 | oui | positive, sans borne, asymétrique : log |
| Délai de livraison moyen (jours) | 3.86 | -0.00 | oui | positive, sans borne, asymétrique : log |
| Écart à la date promise (jours) | 2.39 | — | non | valeurs négatives : hors de la règle |

## 2. Seuils d'écrêtage (0,5e et 99,5e centiles, appris sur les 80 %)

Seuils ramenés dans l'unité d'origine. Clients touchés = clients d'apprentissage.

| variable | seuil bas | seuil haut | touchés en bas | touchés en haut |
|---|---|---|---|---|
| Récence (jours) | 3.00 | 521.00 | 232 | 320 |
| Fréquence (commandes) | 1.00 | 2.00 | 0 | 149 |
| Montant (R$) | 9.90 | 1 359.00 | 276 | 324 |
| Part des frais de port | 0.02 | 0.64 | 325 | 325 |
| Mensualités moyennes | 1.00 | 10.00 | 0 | 221 |
| Articles par commande | 1.00 | 4.00 | 0 | 287 |
| Délai de livraison moyen (jours) | 1.57 | 55.97 | 325 | 325 |
| Écart à la date promise (jours) | -40.00 | 28.00 | 286 | 298 |

## 3. Clients écrêtés sur au moins une variable

| groupe | clients | écrêtés (≥ 1 variable) | % |
|---|---|---|---|
| apprentissage (80 %) | 64 805 | 3 156 | 4.87 |
| mis de côté (20 %) | 16 201 | 792 | 4.89 |

| groupe | 0 variable | 1 variable | 2 variables | 3 ou plus |
|---|---|---|---|---|
| 80 % | 61 649 | 2 636 | 506 | 14 |
| 20 % | 15 409 | 672 | 120 | 0 |

Pour comparaison (option écartée) : à 1 / 99, 5 868 clients d'apprentissage (9.05 %) auraient été écrêtés sur au moins une variable.

## 4. Après préparation

Sur les 80 %, chaque variable doit avoir une moyenne de 0 et un écart-type de 1 (par construction). Sur les 20 %, des valeurs proches de 0 et 1 montrent que les paramètres se transposent bien à des clients jamais vus.

| variable | asymétrie après | moyenne 80 % | écart-type 80 % | moyenne 20 % | écart-type 20 % |
|---|---|---|---|---|---|
| Récence (jours) | 0.47 | -0.000 | 1.000 | -0.005 | 0.996 |
| Fréquence (commandes) | 5.53 | 0.000 | 1.000 | 0.000 | 1.000 |
| Montant (R$) | 0.24 | -0.000 | 1.000 | 0.002 | 1.003 |
| Part des frais de port | 1.01 | 0.000 | 1.000 | -0.003 | 1.002 |
| Mensualités moyennes | 0.77 | 0.000 | 1.000 | -0.013 | 0.996 |
| Articles par commande | 3.39 | 0.000 | 1.000 | 0.002 | 1.011 |
| Délai de livraison moyen (jours) | -0.06 | 0.000 | 1.000 | -0.001 | 0.998 |
| Écart à la date promise (jours) | 0.73 | -0.000 | 1.000 | 0.005 | 0.994 |
