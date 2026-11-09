# ACP normée

Rapport généré par `scripts/analyser_acp.py`. ACP apprise sur les 64 805 clients d'apprentissage préparés (80 %), enregistrée dans `models/acp.json`, puis appliquée telle quelle aux 16 201 clients mis de côté. Règles fixées et poussées avant le calcul (voir `docs/CHOIX.md`).

État : ACP recalculée identique au fichier enregistré.

## 1. Valeurs propres

| axe | valeur propre | % de l'information | % cumulé | > 1 (Kaiser) |
|---|---|---|---|---|
| F1 | 2.011 | 25.13 | 25.13 | oui |
| F2 | 1.486 | 18.58 | 43.71 | oui |
| F3 | 1.072 | 13.40 | 57.11 | oui |
| F4 | 1.028 | 12.85 | 69.97 | oui |
| F5 | 0.962 | 12.03 | 81.99 | non |
| F6 | 0.781 | 9.76 | 91.75 | non |
| F7 | 0.534 | 6.67 | 98.42 | non |
| F8 | 0.126 | 1.58 | 100.00 | non |

## 2. Nombre d'axes retenus

| règle | nombre d'axes | rôle |
|---|---|---|
| Kaiser (valeur propre > 1) | 4 | décide (avec la part cumulée) |
| part cumulée ≥ 70 % | 5 | décide (avec Kaiser) |
| coude (plus forte chute après l'axe) | 1 | indicatif seulement |
| **décision : max(Kaiser, part cumulée)** | **5** |  |

Les 5 axes retenus portent 81.99 % de l'information.

## 3. Corrélations variables–axes

Corrélation entre chaque variable préparée et chaque axe. En gras : axes retenus.

| variable | **F1** | **F2** | **F3** | **F4** | **F5** | F6 | F7 | F8 |
|---|---|---|---|---|---|---|---|---|
| Récence | -0.01 | -0.02 | -0.13 | 0.90 | 0.35 | -0.23 | 0.06 | 0.01 |
| Fréquence | 0.17 | 0.01 | 0.52 | -0.26 | 0.79 | 0.01 | 0.06 | -0.03 |
| Montant | 0.93 | 0.05 | 0.04 | -0.03 | -0.03 | -0.16 | -0.20 | 0.24 |
| Part frais port | -0.85 | 0.07 | 0.33 | 0.14 | -0.00 | 0.30 | -0.06 | 0.22 |
| Mensualités | 0.61 | 0.05 | 0.05 | 0.25 | -0.06 | 0.72 | 0.20 | -0.03 |
| Articles/commande | 0.15 | -0.06 | 0.81 | 0.23 | -0.45 | -0.22 | 0.07 | -0.07 |
| Délai livraison | 0.01 | 0.87 | 0.07 | 0.12 | 0.02 | 0.09 | -0.46 | -0.09 |
| Écart date promise | -0.01 | 0.85 | -0.05 | -0.10 | -0.05 | -0.18 | 0.48 | 0.06 |

## 4. cos² des variables sur les axes retenus

cos² = corrélation au carré : part de la variable expliquée par l'axe. La somme sur les axes retenus mesure la qualité de représentation de la variable.

| variable | F1 | F2 | F3 | F4 | F5 | somme (qualité) |
|---|---|---|---|---|---|---|
| Récence | 0.00 | 0.00 | 0.02 | 0.80 | 0.12 | 0.94 |
| Fréquence | 0.03 | 0.00 | 0.27 | 0.07 | 0.63 | 1.00 |
| Montant | 0.87 | 0.00 | 0.00 | 0.00 | 0.00 | 0.88 |
| Part frais port | 0.72 | 0.01 | 0.11 | 0.02 | 0.00 | 0.85 |
| Mensualités | 0.37 | 0.00 | 0.00 | 0.06 | 0.00 | 0.44 |
| Articles/commande | 0.02 | 0.00 | 0.66 | 0.05 | 0.20 | 0.94 |
| Délai livraison | 0.00 | 0.75 | 0.01 | 0.01 | 0.00 | 0.77 |
| Écart date promise | 0.00 | 0.72 | 0.00 | 0.01 | 0.00 | 0.74 |

## 5. Contributions des variables aux axes retenus (%)

| variable | F1 | F2 | F3 | F4 | F5 |
|---|---|---|---|---|---|
| Récence | 0.0 | 0.0 | 1.6 | 78.2 | 12.7 |
| Fréquence | 1.4 | 0.0 | 25.2 | 6.5 | 65.5 |
| Montant | 43.3 | 0.2 | 0.2 | 0.1 | 0.1 |
| Part frais port | 35.8 | 0.3 | 10.3 | 1.8 | 0.0 |
| Mensualités | 18.3 | 0.2 | 0.2 | 6.0 | 0.4 |
| Articles/commande | 1.1 | 0.3 | 61.7 | 5.0 | 21.1 |
| Délai livraison | 0.0 | 50.7 | 0.5 | 1.4 | 0.1 |
| Écart date promise | 0.0 | 48.4 | 0.3 | 1.0 | 0.2 |

## 6. Description des axes retenus (base de leur nom)

Variables retenues pour nommer un axe : |corrélation| ≥ 0.5, sinon les 2 plus fortes.

**F1** (25.13 %) — |corrélation| ≥ 0.5 : Montant (0.93), Part frais port (-0.85), Mensualités (0.61)

- côté + : Montant élevé, Part frais port faible, Mensualités élevé
- côté − : Montant faible, Part frais port élevé, Mensualités faible

**F2** (18.58 %) — |corrélation| ≥ 0.5 : Délai livraison (0.87), Écart date promise (0.85)

- côté + : Délai livraison élevé, Écart date promise élevé
- côté − : Délai livraison faible, Écart date promise faible

**F3** (13.40 %) — |corrélation| ≥ 0.5 : Articles/commande (0.81), Fréquence (0.52)

- côté + : Articles/commande élevé, Fréquence élevé
- côté − : Articles/commande faible, Fréquence faible

**F4** (12.85 %) — |corrélation| ≥ 0.5 : Récence (0.90)

- côté + : Récence élevé
- côté − : Récence faible

**F5** (12.03 %) — |corrélation| ≥ 0.5 : Fréquence (0.79)

- côté + : Fréquence élevé
- côté − : Fréquence faible

## 7. Vérification de l'axe du temps

Axe du temps si |corr(Récence, axe)| ≥ 0.5 ET |corr(coordonnées, date du premier achat)| ≥ 0.5. Les autres variables qui pèsent (|corr| ≥ 0,3) sont décrites, sans être une condition.

| axe | corr. Récence | corr. date d'achat | axe du temps | autres variables (|corr| ≥ 0,3) |
|---|---|---|---|---|
| F1 | -0.01 | -0.01 | non | Montant (0.93), Part frais port (-0.85), Mensualités (0.61) |
| F2 | -0.02 | 0.02 | non | Délai livraison (0.87), Écart date promise (0.85) |
| F3 | -0.13 | 0.08 | non | Fréquence (0.52), Part frais port (0.33), Articles/commande (0.81) |
| F4 | 0.90 | -0.86 | **oui** | — |
| F5 | 0.35 | -0.42 | non | Fréquence (0.79), Articles/commande (-0.45) |

## 8. Projection des 20 % mis de côté

Variance des coordonnées : sur les 80 %, elle vaut la valeur propre (par construction) ; sur les 20 %, des valeurs proches montrent que les axes se transposent à des clients jamais vus.

| axe | valeur propre | variance 80 % | variance 20 % | moyenne 20 % |
|---|---|---|---|---|
| F1 | 2.011 | 2.011 | 2.011 | -0.002 |
| F2 | 1.486 | 1.486 | 1.470 | 0.002 |
| F3 | 1.072 | 1.072 | 1.082 | 0.001 |
| F4 | 1.028 | 1.028 | 1.020 | -0.008 |
| F5 | 0.962 | 0.962 | 0.975 | -0.002 |

## 9. Noms des axes retenus

| axe | nom | % de l'information |
|---|---|---|
| F1 | Valeur de l'achat | 25.13 |
| F2 | Expérience de livraison | 18.58 |
| F3 | Taille du panier | 13.40 |
| F4 | Ancienneté de l'achat (axe du temps) | 12.85 |
| F5 | Réachat (plutôt qu'achat groupé) | 12.03 |

## 10. Stabilité des axes par bootstrap (description)

50 tirages avec remise des 64 805 clients d'apprentissage (graine 42) ; l'ACP est refaite sur chaque tirage. |cos| = 1 : axe identique ; un |cos| bas avec un « meilleur |cos| » haut signifie que l'axe existe toujours mais a changé de rang.

| axe | |cos| médian (même rang) | |cos| 5e centile | |cos| minimum | meilleur |cos| médian | meilleur |cos| 5e centile | valeur propre : médiane [5e – 95e centile] |
|---|---|---|---|---|---|---|
| F1 | 1.000 | 1.000 | 0.999 | 1.000 | 1.000 | 2.013 [1.991 – 2.026] |
| F2 | 1.000 | 1.000 | 0.999 | 1.000 | 1.000 | 1.490 [1.470 – 1.514] |
| F3 | 0.991 | 0.945 | 0.900 | 0.991 | 0.945 | 1.077 [1.056 – 1.095] |
| F4 | 0.990 | 0.951 | 0.900 | 0.990 | 0.951 | 1.027 [1.019 – 1.037] |
| F5 | 0.992 | 0.954 | 0.937 | 0.992 | 0.954 | 0.963 [0.936 – 0.982] |
| F6 | 1.000 | 0.999 | 0.998 | 1.000 | 0.999 | 0.781 [0.776 – 0.786] |

**Sous-espaces** : plus petit cosinus principal entre le sous-espace d'origine et celui du tirage (1 = même sous-espace, même si les axes y ont tourné).

| sous-espace | médiane | 5e centile | minimum |
|---|---|---|---|
| F1 – F2 | 0.9998 | 0.9997 | 0.9995 |
| F3 – F5 | 0.9995 | 0.9989 | 0.9985 |
| F1 – F5 | 0.9996 | 0.9989 | 0.9985 |

**Nombre d'axes que donnerait la règle sur chaque tirage** : 4 axes : 22 tirages, 5 axes : 28 tirages. (Description : la décision reste celle calculée sur les 80 %.)
