# Journal des choix

Chaque choix est noté avec sa date, ce qui a été décidé et pourquoi.

## 2026-11-09 – Mise en place du dépôt

- **Jeu de données** : n°3 du catalogue, *Brazilian E-Commerce Public Dataset by Olist* (Kaggle).
  Étiquette externe : `review_score`. Elle n'entre jamais dans le clustering ; elle sert
  uniquement à l'évaluation des segments (indices externes).
- **Python 3.11**, versions des bibliothèques épinglées, environnement `.venv`.
- **Fins de ligne** : `.gitattributes` force LF pour le texte, JSON et CSV figés, et marque
  les modèles (`.joblib`, `.pkl`…) comme binaires. Raison : au projet précédent, un fichier
  de modèle converti en CRLF sous Windows faisait planter l'API dans un clone neuf.
- **Données brutes** non versionnées (`data/raw/` ignoré) : elles sont téléchargées par un script.
- **Graine aléatoire** unique (42) pour tous les tirages : résultats reproductibles.
- **Mémoire** : 15,7 Go de RAM au total, environ 1,8 Go libres avec Chrome ouvert
  (mesure du 2026-11-09). La CAH demande une mémoire en n² : elle sera faite sur un
  échantillon si nécessaire.
- **Fichiers ignorés** : seul le PDF du sujet est ignoré (par son nom exact), pas tous les PDF,
  car la synthèse `reports/synthese.pdf` sera versionnée. Seul `data/raw/` est ignoré :
  `data/demo/` contiendra de petits exemples, sous la licence du jeu.

## 2026-11-09 – Règles d'évaluation fixées avant tout calcul

- **Règle de choix de k (étape 6a)** : elle est écrite et commitée AVANT de calculer le moindre
  indice (internes, stabilité et externes), pas seulement avant les indices externes.
  Ainsi, la règle ne peut pas être ajustée après coup pour favoriser un résultat.
- **Avis mis à l'écart dès le chargement** : toute la table des avis (`review_score`,
  titres et commentaires, dates de création et de réponse) est rangée à part dès le
  chargement. Aucune de ces colonnes ne peut entrer dans le profil client ni dans le clustering.
- **Indépendance partielle de l'étiquette** : `review_score` n'est pas totalement indépendante
  des variables de délai qui, elles, entrent dans le clustering (un retard de livraison
  entraîne souvent une mauvaise note). Un lien entre segments et notes ne prouvera donc
  pas que les segments « découvrent » la satisfaction : une partie du lien vient de
  variables communes. Ce point sera dit honnêtement dans l'évaluation externe.
- **20 % de clients mis de côté** : dès l'étape 2, 20 % des clients (`customer_unique_id`)
  sont tirés au hasard avec la graine fixe et mis de côté. Transformations, ACP et modèles
  sont appris uniquement sur les 80 % restants. Les 20 % servent à la fin à vérifier
  l'affectation de nouveaux clients (silhouette, répartition par segment).
- **Monnaie** : tous les montants sont en réals brésiliens, notés **R$** dans les
  tableaux, les graphiques, l'API et l'application.

## 2026-11-09 – Étape 1 : source, licence et nature des données

- **Source vérifiée** (métadonnées officielles de la page Kaggle `olistbr/brazilian-ecommerce`,
  lues le 2026-11-09) : titre « Brazilian E-Commerce Public Dataset by Olist », propriétaire
  Olist, licence **CC BY-NC-SA 4.0**, taille totale annoncée **126 186 995 octets**,
  dernière mise à jour 2021-10-01, « 100k orders from 2016 to 2018 ».
- **Données réelles, anonymisées, non synthétiques.** Texte de la page : « This is real
  commercial data, it has been anonymised, and references to the companies and partners
  in the review text have been replaced with the names of Game of Thrones great houses. »
- **Conséquences de la licence** : citer Olist (BY), usage non commercial uniquement (NC),
  tout extrait redistribué (`data/demo/`) garde la licence CC BY-NC-SA 4.0 (SA).
  Le README le dira ainsi, avec le remerciement « Thanks to Olist for releasing this dataset. »
  Le code du projet peut avoir sa propre licence, distincte de celle des données.
- **Téléchargement sans jeton** : l'adresse publique de téléchargement Kaggle renvoie le zip
  sans connexion. Aucun jeton n'est donc nécessaire ni stocké.
- **Deux fichiers de dépendances** : `requirements.txt` (ce qu'il faut pour faire tourner le
  projet) et `requirements-dev.txt` (tests et outils de travail ; il inclut le premier).

## 2026-11-09 – Décisions issues du contrôle qualité

- **Commandes livrées seulement** : le profil client est construit sur les commandes au
  statut `delivered` ayant une date de livraison au client (96 470 commandes). Raison : les
  délais n'existent pas sans livraison. Effet mesuré : **2 746 clients sur 96 096 (2,86 %)**
  n'ont aucune commande livrée et disparaissent ; il en reste 93 350. Les 775 commandes sans
  article sont toutes non livrées : elles sont écartées par la même règle.
- **Vrai client** = `customer_unique_id` (un `customer_id` est créé à chaque commande).
- **Montant = somme des prix des articles** (R$), sans frais de port ni intérêts de
  paiement. Les frais de port et le nombre de mensualités seront des variables séparées
  (décision à l'étape 2), pour ne pas mélanger trois informations dans une seule.
- **Anomalies de dates conservées** : 166 remises au transporteur avant l'achat et 23
  livraisons avant la remise au transporteur (moins de 0,2 %). Elles touchent peu le délai
  client (achat → livraison), seul utilisé. Les 8 commandes livrées sans date sont exclues.
- **Produits sans catégorie** (610) : catégorie « inconnue ». Les 2 catégories sans
  traduction (`pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`) sont traduites à la main.
- **Table de géolocalisation** non utilisée (261 831 doublons exacts) : l'État du client suffit.
- **Note d'avis par client** : la règle qui ramène les notes (par commande) au client sera
  écrite avec la règle de choix de k (étape 6a), avant tout calcul d'indice. Constats à
  prendre en compte : 768 commandes sans avis, 547 avec plusieurs avis, 789 avis rattachés
  à plusieurs commandes.
- **Déploiement** : Python 3.11.0 en local ; sur Render, `PYTHON_VERSION=3.11.9`.

## 2026-11-09 – Exploration : État, Récence et coupure de fin de période

- **État du client : description seulement**, jamais dans le clustering. Raisons : 27 modalités
  (en 0/1, les distances seraient dominées par « même État ou non » et les segments
  deviendraient une carte) ; la géographie est déjà portée par les délais et les frais de port
  (délai médian 7,2 j à SP contre 25,9 j en AM) ; ACP normée, CAH et K-Means demandent des
  variables numériques. L'État apparaîtra dans les profils de segments et les explications.
- **Interprétation de la Récence** : 96,9 % des clients n'ont qu'une commande ; la Récence revient
  donc presque à la date de leur unique achat. À l'étape 2, elle se lira « a acheté il y a
  longtemps », et non forcément « client qui se désintéresse ».
- **Début de période : 2017-01-01** (validé). Fin 2016 = période d'essai (4, 324, 0 et 1 commandes
  de septembre à décembre), séparée du reste par deux mois presque vides.
- **Coupure de l'extraction constatée** (détail dans `reports/exploration.md`) : les livraisons
  s'arrêtent net après la semaine du 2018-08-27 au 2018-09-02 (1 607 livraisons, puis 28 la
  semaine suivante). Les commandes de fin de période ne peuvent donc pas avoir de livraison
  lente. Effets visibles sur août 2018 : délai médian 7,0 j et 90e centile 13,1 j (contre
  11,1 j et 23,1 j en moyenne de janvier 2017 à mai 2018) ; délai *promis* médian 14 j
  (contre 22 à 28 j), alors qu'il est fixé à l'achat : des commandes à long délai
  manquent entièrement ; part de SP 49,8 % (contre 40 à 46 %). La part de commandes livrées,
  elle, ne baisse pas (97,5 %) : la coupure retire des commandes au lieu de les laisser
  « en route ».
- **Fin de période : dernier achat gardé le 2018-06-30 ; Récence comptée à partir du
  2018-07-01** (validé ; `config.FIN_ACHATS` et `config.DATE_REFERENCE`). Raisons chiffrées :
  - sur la période normale (achats de janvier 2017 à mai 2018), 99 % des livraisons arrivent
    en **47,8 jours** ou moins ; un achat du 2018-06-30 dispose de **65 jours** avant la
    coupure (2018-09-03) : juin est complet. Un achat de fin juillet n'a que 34 jours ;
  - juin ne montre aucun signe de commandes manquantes : délai promis médian 28 j (normal),
    part de SP 44,9 % (normal). Juillet en montre déjà (délai promis 20 j), août nettement
    (14 j, 49,8 % de SP) ;
  - coût : **81 006 clients gardés**, soit une perte de 12 090 clients (**13,0 %**) par rapport
    aux 93 096 clients de 2017-01 → 2018-08. Depuis les 93 350 clients ayant au moins une
    commande livrée, la perte totale due à la période est de 12 344 (13,2 %), dont 254 de 2016.
  - Limites notées : les délais de juin restent courts (médiane 8,0 j) alors que la coupure
    ne peut pas l'expliquer (marge 65 j) : c'est un trait de la période, sans cause supposée.
    La semaine de livraison du 16 au 22 juillet 2018 est anormalement creuse (367 livraisons) :
    hors période, sans effet.
- **Chaîne de clients retenus** : 96 096 vrais clients → 93 350 avec au moins une commande
  livrée → **81 006** avec une commande livrée achetée dans la période (83 696 commandes).
- **Sorties console protégées** (`segmentation/console.py`) : sous Windows, une sortie redirigée
  est encodée en cp1252, qui ne connaît pas « → » ou « ≥ » ; le script plantait. Un caractère
  impossible à écrire est désormais remplacé par « ? ».

## 2026-11-09 – Étape 2 : profil client et mise de côté des 20 %

- **Une ligne par vrai client** (`customer_unique_id`), calculée sur les commandes livrées (avec
  date) achetées du 2017-01-01 au 2018-06-30 : **81 006 clients**, 83 696 commandes.
- **8 variables pour le clustering** (`config.VARIABLES_PROFIL`) :
  Récence (jours depuis le dernier achat, comptés au 2018-07-01), Fréquence (commandes livrées),
  Montant (somme des **prix des articles**, en R$, sans frais de port), part des frais de port
  (frais / (prix + frais)), mensualités moyennes, articles par commande, délai de livraison
  moyen (jours), écart moyen à la date promise (jours, > 0 = retard).
- **Fréquence gardée** (F du RFM demandé par le sujet) malgré 97 % de clients à 1 commande ;
  son traitement (log, écrêtage) sera décidé à l'étape 3 avec les autres valeurs extrêmes.
- **Part des frais de port plutôt que leur total** : le total était corrélé à 0,47 avec le
  Montant ; la part apporte une information différente (distance, objets lourds).
- **Moyen de paiement seulement pour décrire** : une part payée par *boleto* aurait chevauché
  les mensualités (un *boleto* se paie en une fois).
- **Écartés** : nombre de vendeurs (1 pour 98,7 % des commandes), panier moyen (presque égal au
  Montant), toute donnée d'avis.
- **Colonnes de description** (jamais dans le clustering) : État de la dernière commande,
  catégorie principale (celle qui pèse le plus en prix), moyen de paiement principal (celui qui
  pèse le plus en montant payé), date du premier achat. En cas d'égalité, la première par ordre
  alphabétique (reproductible). Les 2 lignes de paiement à 0 mensualité comptent pour 1.
- **Calcul du profil avant le tirage, sans fuite** : chaque valeur d'un client ne dépend que de
  ses propres commandes. Tout ce qui utilise des statistiques de plusieurs clients
  (standardisation, seuils, ACP, modèles) sera appris sur les 80 % seulement, dès l'étape 3.
- **Tirage des 20 %** : par client ; identifiants triés puis mélangés avec la graine 42 ;
  **64 805 clients d'apprentissage, 16 201 mis de côté**. L'empreinte SHA-256 de la liste mise
  de côté est versionnée dans `docs/tirage_empreinte.json` (la liste elle-même ne l'est pas) ;
  un test vérifie qu'elle ne change pas. Les deux groupes se ressemblent : écart standardisé
  ≤ 0,011 sur les 8 variables, 2,98 % de clients à plusieurs commandes des deux côtés.
- **Données dérivées non versionnées** : `data/processed/` ajouté au `.gitignore`.
- **À vérifier à l'étape 4 (ACP)** : avec 97 % de clients à une seule commande, la Récence revient
  à la date d'achat ; or les délais ont aussi baissé en 2018. Un axe de l'ACP pourrait donc ne
  mesurer que « le temps » (achat ancien et livraison lente contre achat récent et livraison
  rapide). Le vérifier et le dire si c'est le cas.
- **À rappeler lors de l'évaluation externe** : les variables de délai (délai moyen, écart à la
  date promise) entrent dans le clustering et sont liées à la note d'avis (un retard entraîne
  souvent une mauvaise note). Les segments seront donc en partie rapprochés de la note par
  construction ; il faudra le dire honnêtement.

## 2026-11-09 – Étape 3 : règles de préparation, fixées avant tout segment

Ces règles sont fixées à partir de la **forme des données des 80 % d'apprentissage seulement**
(asymétries, centiles), avant toute ACP, tout clustering, tout indice et toute lecture des avis.

- **Règle de non-retour.** Les transformations ci-dessous (variables passées au log, seuils
  d'écrêtage, standardisation, absence de pondération) ne sont pas modifiées pour obtenir de
  « plus beaux » segments ou de meilleurs indices. Toute modification ultérieure exige une raison
  écrite et datée dans ce journal, et cette raison ne peut pas être l'apparence des segments ni
  la valeur d'un indice.
- **Règle du log, sans exception.** On applique `log(1 + x)` aux variables positives et sans
  borne haute (montants, durées, comptages), si leur asymétrie dépasse 1 et si le log la réduit.
  Asymétries mesurées sur les 80 % (brute → après log) :
  - dans la règle, log appliqué : Montant (10,00 → 0,27), mensualités moyennes (1,59 → 0,79),
    délai de livraison moyen (3,86 → 0,00), Fréquence (9,16 → 6,48), articles par commande
    (7,49 → 3,95) ;
  - hors de la règle par définition : part des frais de port (proportion bornée entre 0 et 1),
    écart à la date promise (valeurs négatives) ;
  - hors de la règle par son asymétrie : Récence (0,47, inférieure à 1).
- **Écrêtage** des 8 variables aux **0,5e et 99,5e centiles**, appris sur les 80 %, calculés
  après le log : toute valeur au-delà est ramenée au seuil. Raisons du choix de cette option
  parmi les quatre du sujet : tous les clients restent et reçoivent un segment (indispensable
  pour un nouveau client) ; la règle se réapplique avec deux nombres par variable ; « garder »
  laisserait quelques clients (13 440 R$, 188 jours de retard) peser lourd dans des distances au
  carré ; DBSCAN demande des réglages subjectifs, laisse des clients sans segment et ne classe
  pas un nouveau client (il sera testé comme algorithme au module 3) ; « suivre à part »
  retirerait plusieurs pour cent des clients et un nouveau client extrême n'aurait pas de segment.
- **Pourquoi 0,5 / 99,5 et pas 1 / 99** : le but est de neutraliser les vraies queues, pas de
  modifier des clients ordinaires. À 0,5 / 99,5, environ 1 % des clients sont touchés par
  variable et le Montant passe déjà d'un maximum de 13 440 R$ à un plafond d'environ 1 365 R$.
  À 1 / 99, on toucherait deux fois plus de clients pour un gain faible ; exemple mesuré sur
  l'écart à la date promise : 584 clients touchés à 0,5 / 99,5 (bornes −40 / +28 j) contre
  1 207 à 1 / 99 (bornes −35 / +20 j). Sur 8 variables, l'écart se cumule.
- **Indicateur « écrêté à la préparation »** (oui/non, et sur quelles variables) : conservé pour
  la description et l'explication (module 5), jamais dans le clustering.
- **Standardisation** de toutes les variables, `z = (x − moyenne) / écart-type`, moyenne et
  écart-type appris sur les 80 % après log et écrêtage. Ordre fixé : log → écrêtage →
  standardisation.
- **Aucune pondération** : aucun poids ajouté ou retiré à une variable. La Fréquence (qui devient
  en pratique « une / plusieurs commandes » après écrêtage, plafond = 2) et les articles par
  commande peuvent créer des segments à part ; c'est un comportement réel, et ce choix est figé
  avec le reste.
- **Apprendre une fois, réappliquer tel quel** : les paramètres appris (log oui/non, seuils,
  moyennes, écarts-types) sont enregistrés dans `models/preparation.json` (texte, LF) et
  réappliqués sans modification aux 20 % mis de côté et à tout nouveau client.

## 2026-11-09 – Étape 3 : résultats de la préparation

Application des règles ci-dessus, sans modification (détail dans `reports/preparation.md`,
paramètres dans `models/preparation.json`).

- **Log appliqué** à la Fréquence, au Montant, aux mensualités moyennes, aux articles par
  commande et au délai de livraison moyen, conformément à la règle.
- **Clients écrêtés sur au moins une variable** : **3 156 sur 64 805 (4,87 %)** dans
  l'apprentissage, 792 sur 16 201 (4,89 %) parmi les clients mis de côté. Pour comparaison,
  l'option écartée 1 / 99 en aurait touché 5 868 (9,05 %), presque le double. Répartition dans
  l'apprentissage : 2 636 clients sur 1 variable, 506 sur 2, 14 sur 3 ou plus.
- **Seuils dans l'unité d'origine** : Montant de 9,90 à **1 359 R$** (le « environ 1 365 R$ » écrit
  plus haut venait d'un arrondi du seuil sur l'échelle log ; la valeur exacte est 1 359 R$),
  Fréquence plafonnée à 2 (149 clients ramenés à 2), articles par commande plafonnés à 4,
  mensualités à 10, délai moyen de 1,57 à 55,97 jours, écart à la date promise de −40 à
  +28 jours, Récence de 3 à 521 jours, part des frais de port de 0,02 à 0,64.
- **Transposition aux 20 %** : après application des paramètres appris, moyennes entre −0,013 et
  +0,005 et écarts-types entre 0,994 et 1,011 : les paramètres se transposent bien à des clients
  jamais vus.
- **Asymétries restantes** (après préparation) : Fréquence 5,53 et articles par commande 3,39,
  car presque tous les clients valent 1 ; c'est attendu et ne change pas la règle.
- **Vérification de stabilité** : relancer `scripts/preparer.py` recalcule les paramètres et
  s'arrête s'ils diffèrent du fichier enregistré ; un test vérifie aussi qu'ils sont exactement
  ceux appris sur les 80 %.

## 2026-11-09 – Étape 4 : règles de l'ACP, fixées avant tout calcul

Ces règles sont écrites et poussées avant le calcul de la moindre valeur propre. La règle de
non-retour de l'étape 3 s'applique aussi à elles.

- **Apprentissage et projection** : l'ACP normée est apprise sur les 64 805 clients
  d'apprentissage préparés (étape 3). Ses axes (coefficients) et ses valeurs propres sont
  enregistrés dans `models/acp.json` (texte, LF). Les 20 % mis de côté et tout nouveau client
  sont préparés puis projetés avec ces paramètres, sans rien réapprendre.
- **Sens des axes** : convention fixe pour un résultat reproductible ; sur chaque axe, la
  variable au plus grand coefficient en valeur absolue est du côté positif.
- **Nombre d'axes retenus** = le plus grand de ces deux nombres :
  (a) le nombre d'axes de valeur propre strictement supérieure à 1 (Kaiser) ;
  (b) le plus petit nombre d'axes dont la part cumulée de l'information atteint 70 %.
  Le coude est tracé et commenté, mais ne décide pas (subjectif). Si les trois règles
  divergent, le désaccord est expliqué dans le rapport. 70 % plutôt que 80 % : les variables
  sont peu corrélées (au plus 0,47), les valeurs propres seront probablement plates, et 80 %
  risquerait de garder presque tous les axes.
- **Lecture des axes** : cercles des corrélations, tableau des corrélations variables–axes,
  cos² (et leur somme sur les axes retenus = qualité de représentation de chaque variable),
  contributions des variables aux axes.
- **Nom de chaque axe retenu** : il vient des variables dont la corrélation avec l'axe vaut au
  moins 0,5 en valeur absolue ; si aucune n'y arrive, des 2 plus fortes. Les deux pôles
  (côté + et côté −) sont décrits. Le nom est une interprétation et ne modifie aucun calcul.
- **Axe du temps** : un axe retenu est déclaré « axe du temps » si (a) la Récence y a une
  corrélation d'au moins 0,5 en valeur absolue ET (c) les coordonnées des clients sur cet axe
  sont corrélées à la date d'achat (colonne de description `premier_achat`, hors ACP) avec au
  moins 0,5 en valeur absolue. Les autres variables qui pèsent sur cet axe (par exemple les
  délais) sont décrites, sans être une condition. Pour chaque axe retenu, sa corrélation avec la
  date d'achat est donnée, même faible. Si un axe du temps est trouvé, rien n'est modifié ; il
  est signalé dans son nom et dans l'interprétation des segments (module 5).
- **Données utilisées à l'étape 5** : K-Means (plusieurs initialisations) et CAH de Ward
  (dendrogramme, corrélation cophénétique) sur les **8 variables préparées** ; classification
  mixte (CAH sur un échantillon, puis consolidation par K-Means sur tous les clients
  d'apprentissage à partir des centres de la CAH) et HDBSCAN sur les **axes retenus** de l'ACP.
  Les axes **ne sont pas restandardisés** : leurs coordonnées gardent leur étalement (égal à la
  valeur propre), sinon un petit axe pèserait autant que le premier. La taille de l'échantillon
  de la CAH sera fixée au début de l'étape 5 d'après la mémoire libre mesurée, avec la graine 42,
  sur les 80 % seulement.
