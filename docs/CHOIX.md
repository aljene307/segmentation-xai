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

## 2026-11-09 – Étape 4 : résultats de l'ACP

Application des règles fixées et poussées avant le calcul (commit « Fixer les règles de l'ACP
avant tout calcul »), sans modification. Détail dans `reports/acp.md`, paramètres dans
`models/acp.json`.

- **Valeurs propres** : 2,011 ; 1,486 ; 1,072 ; 1,028 ; 0,962 ; 0,781 ; 0,534 ; 0,126.
  Parts cumulées : 25,1 % ; 43,7 % ; 57,1 % ; **69,97 %** ; 82,0 % ; 91,8 % ; 98,4 % ; 100 %.
- **Décision : 5 axes retenus** (81,99 % de l'information). Kaiser donne 4, la part cumulée 5,
  donc max = 5. Désaccord expliqué : F4 atteint 69,97 %, juste sous le seuil de 70 % ; la règle
  fixée d'avance impose donc F5, qui porte surtout la Fréquence (cos² 0,63). Le coude indicatif
  est après F1 (plus forte chute 2,011 → 1,486), mais les valeurs propres de F3 à F5 sont presque
  plates (1,07 ; 1,03 ; 0,96) : il n'y a pas de coude net, ce qui confirme que le coude ne pouvait
  pas décider. Ce cas, tranché à 0,03 point près, montre l'intérêt d'avoir fixé la règle avant.
- **Description des axes** (variables à |corrélation| ≥ 0,5) :
  F1 (25,1 %) Montant +0,93, part des frais de port −0,85, mensualités +0,61 ;
  F2 (18,6 %) délai de livraison +0,87, écart à la date promise +0,85 ;
  F3 (13,4 %) articles par commande +0,81, Fréquence +0,52 ;
  F4 (12,9 %) Récence +0,90 ;
  F5 (12,0 %) Fréquence +0,79.
- **Axe du temps : F4**, selon la règle fixée (corrélation avec la Récence 0,90, avec la date
  d'achat −0,86). C'est la Récence presque seule : les délais n'y pèsent pas (0,12 et −0,10) et
  restent sur F2, qui n'est pas lié à la date (0,02). La crainte d'un axe mêlant « achat ancien »
  et « livraison lente » ne se vérifie donc pas. Corrélations des autres axes avec la date
  d'achat : F1 −0,01 ; F2 0,02 ; F3 0,08 ; F5 −0,42 (F5 contient aussi la Récence, 0,35).
  Conséquence, sans rien modifier : un segment séparé surtout par F4 signifiera « clients d'une
  autre période d'achat », pas un comportement différent ; à dire au module 5.
- **Qualité de représentation sur les 5 axes** : bonne pour 7 variables (0,74 à 1,00) ; faible
  pour les **mensualités (0,44)**, dont la part propre est surtout sur F6 (cos² 0,52), écarté.
  Conséquence pour l'étape 5 : la classification mixte (sur les axes) perd une partie de
  l'information sur les mensualités ; K-Means et la CAH sur les 8 variables la gardent. À
  rappeler dans le tableau comparatif.
- **Nuage continu** : sur le plan F1–F2, les clients forment un seul nuage, sans groupes
  séparés à l'œil. Les segments découperont probablement un continuum plutôt que de révéler des
  groupes nettement isolés ; des silhouettes modérées seront donc attendues. C'est un constat,
  pas une raison de modifier quoi que ce soit.
- **Projection des 20 %** : variance des coordonnées axe par axe, à comparer à la valeur propre
  (= variance sur les 80 %) : F1 2,011 contre 2,011 ; F2 1,470 contre 1,486 ; F3 1,082 contre
  1,072 ; F4 1,020 contre 1,028 ; F5 0,975 contre 0,962. Écart relatif au plus 1,4 % (F5) ;
  moyennes entre −0,008 et +0,002. Les axes se transposent bien. (Une première rédaction disait
  « entre 1,470 et 2,011 » : erreur, le minimum est 0,975, sur F5.)
- **Stabilité des axes par bootstrap** (description, aucune règle modifiée) : 50 tirages avec
  remise des 64 805 clients d'apprentissage, graine 42, ACP refaite à chaque tirage ; on compare
  chaque axe du tirage à l'axe de même rang d'origine (|cosinus|, 1 = identique).
  - F1 et F2 : |cos| médian 1,000, minimum 0,999 : parfaitement stables. F6 aussi (0,998 au
    minimum).
  - F3, F4, F5 : |cos| médian 0,991 / 0,990 / 0,992 ; 5e centile 0,945 / 0,951 / 0,954 ;
    minimum 0,900 / 0,900 / 0,937. Ces trois axes **tournent légèrement entre eux** (jusqu'à
    environ 26° dans le pire tirage), comme attendu avec des valeurs propres proches, mais ils
    **ne changent jamais de rang** : le meilleur |cos| est toujours celui du même rang, et les
    intervalles des valeurs propres ne se chevauchent pas (F3 [1,056 – 1,095], F4 [1,019 – 1,037],
    F5 [0,936 – 0,982], 5e – 95e centiles).
  - **Sous-espaces** (plus petit cosinus principal ; 1 = même sous-espace même si les axes y
    tournent) : F1–F2 0,9997 au 5e centile ; F3–F5 0,9989 ; **F1–F5 0,9989** (minimum 0,9985,
    soit environ 3°). Le sous-espace des 5 axes retenus est donc très stable.
  - **Conséquence pour les noms de F3 à F5** : ils restent valables (chaque axe garde sa variable
    dominante dans presque tous les tirages), mais ils décrivent une tendance dominante, pas une
    frontière nette : une petite part de chacun se mélange aux deux autres. On lira donc la
    coordonnée d'un client sur F3, F4 ou F5 avec prudence, et on décrira les segments d'abord par
    leurs variables d'origine (module 5), les axes servant de résumé.
  - **Conséquence pour la classification mixte** : elle n'utilise que les distances dans le
    sous-espace F1–F5, qui ne changent pas quand les axes tournent à l'intérieur de ce
    sous-espace. Le sous-espace étant stable, la rotation de F3 à F5 n'affecte pas la
    classification.
  - **Le nombre d'axes lui-même est fragile** : sur les 50 tirages, la règle aurait donné 4 axes
    22 fois et 5 axes 28 fois, parce que la part cumulée à F4 (69,97 %) est collée au seuil de
    70 %. La décision reste 5 axes (règle fixée, calculée sur les 80 %). Ce point sera rappelé
    dans le tableau comparatif de l'étape 5 ; K-Means et la CAH sur les 8 variables, qui ne
    dépendent pas de ce choix, servent de point de comparaison.
- **Noms des axes retenus** (validés ; interprétation, ne modifie aucun calcul ; dans
  `config.NOMS_AXES`) : F1 « Valeur de l'achat », F2 « Expérience de livraison », F3 « Taille du
  panier », F4 « Ancienneté de l'achat (axe du temps) », F5 « Réachat (plutôt qu'achat groupé) ».

## 2026-11-09 – Règles du choix de k, de la note d'avis et de l'évaluation externe

Ces règles sont écrites, commitées et poussées **avant tout calcul de partition** (étape 5) et
avant toute lecture de la table des avis. La règle de non-retour s'applique à elles : toute
modification exige une raison écrite et datée, qui ne peut pas être l'apparence des segments ni
la valeur d'un indice.

### Méthode de référence pour la segmentation finale

- **K-Means sur les 8 variables préparées**, appris sur les 64 805 clients d'apprentissage.
- **Pourquoi pas la classification mixte, que le cours met en avant.** Sur un jeu où les
  premiers axes de l'ACP résument très bien les données, la classification mixte est préférable :
  elle travaille sur l'essentiel et écarte le bruit des derniers axes. Ici, deux constats de
  l'étape 4 vont contre ce choix :
  - **les mensualités sont mal représentées sur les 5 axes retenus** (qualité 0,44) : leur part
    propre est surtout sur F6 (cos² 0,52), qui est écarté. Une segmentation sur les axes perdrait
    donc une partie de l'information sur le paiement en plusieurs fois, qui est utile aux
    équipes commerciales ;
  - **le nombre d'axes est fragile** : la part cumulée à F4 (69,97 %) est collée au seuil de
    70 %, et la règle aurait donné 4 axes dans 22 tirages bootstrap sur 50. Une segmentation
    finale qui dépendrait de ce choix hériterait de cette fragilité.
  K-Means sur les 8 variables utilise toute l'information et ne dépend pas du nombre d'axes. Il
  traite tous les clients, et un nouveau client s'affecte simplement au centre le plus proche.
- **La classification mixte reste calculée et comparée** (avec 5 axes, et avec 4 axes en
  contrôle de sensibilité), comme la CAH de Ward et HDBSCAN. Le tableau comparatif montrera
  l'accord entre la mixte et K-Means (ARI) ; si l'accord est élevé, les deux voies mènent aux
  mêmes segments. Ces méthodes ne décident pas du nombre de segments.

### Règle de choix de k (k de 2 à 8), appliquée à la méthode de référence

1. **Calculs pour chaque k de 2 à 8** :
   - indices internes : R² (= 1 − inertie intra-classe / inertie totale), silhouette (sur un
     échantillon fixe de 8 000 clients d'apprentissage, graine 42, le même pour tous les k),
     Calinski-Harabasz et Davies-Bouldin (sur les 64 805 clients) ;
   - stabilité par bootstrap, calcul exact, pour chaque k :
     1. la **partition de référence** est celle de K-Means (20 initialisations, graine 42) sur
        les 64 805 clients d'apprentissage ;
     2. **50 tirages** : chaque tirage prend 64 805 clients d'apprentissage au hasard **avec
        remise** (un client peut être tiré plusieurs fois, d'autres pas du tout), avec un
        générateur initialisé une fois par la graine 42 ;
     3. sur chaque tirage, **K-Means est refait** (k-means++, 10 initialisations, graine propre
        au tirage, dérivée du générateur) ;
     4. **tous les 64 805 clients d'apprentissage** (et pas seulement ceux du tirage) sont
        affectés au centre le plus proche **parmi les centres du tirage** ;
     5. **ARI** entre cette partition et la partition de référence ; on retient l'ARI moyen sur
        les 50 tirages (et son minimum, donné pour information) ;
     6. **Jaccard par segment** : pour chaque segment de référence A et chaque segment B de la
        partition du tirage, Jaccard(A, B) = (nombre de clients dans A et B) / (nombre de
        clients dans A ou B). Le segment A est **apparié au segment B du tirage avec le Jaccard
        le plus élevé** (deux segments de référence peuvent être appariés au même B : c'est
        alors un signe d'instabilité, qui abaisse leur Jaccard). On retient, pour chaque segment
        de référence, le Jaccard moyen sur les 50 tirages.
     L'ARI compare toute la partition et ne dépend pas des numéros des segments ; le Jaccard
     dit quel segment est fragile.
2. **Admissibilité** (conditions obligatoires) : un k est admissible si
   (a) chaque segment contient au moins **2 % des clients d'apprentissage** (1 297 clients) ;
   (b) l'**ARI bootstrap moyen vaut au moins 0,80** ;
   (c) chaque segment a un **Jaccard moyen d'au moins 0,60**.
   Raisons : 2 % est la plus petite taille qui reste actionnable pour une campagne, sans exclure
   d'avance un segment de clients qui recommandent (3 % des clients). Pour le Jaccard, on suit
   Hennig (2007, « Cluster-wise assessment of cluster stability », *Computational Statistics &
   Data Analysis*) : un Jaccard moyen inférieur ou égal à 0,5 indique un segment « dissous » ;
   de 0,6 à 0,75, le segment montre une tendance (un motif réel, aux contours mal définis) ;
   au-dessus de 0,75, il est stable ; au-dessus de 0,85, très stable. **0,60 est donc une
   exigence modérée** : elle accepte un segment qui ne fait que montrer une tendance. Ce choix
   est assumé et adapté à nos données : l'ACP a montré un nuage continu, sans groupes séparés,
   et des frontières nettes n'y sont pas attendues. Exiger 0,75 risquerait de n'admettre aucun
   k ; la règle 5 couvre de toute façon ce cas. Pour l'ARI, 0,80 demande que la partition
   d'ensemble soit très largement reproduite d'un tirage à l'autre.
3. **Choix parmi les k admissibles** : chaque k reçoit un rang pour la silhouette (la plus
   haute = rang 1), Calinski-Harabasz (le plus haut = rang 1) et Davies-Bouldin (le plus bas =
   rang 1). **Le k dont la somme des trois rangs est la plus petite est retenu** ; en cas
   d'égalité, le plus petit k. Le R² est tracé et commenté (il augmente toujours avec k), sans
   rang.
4. **Utilité métier** : les segments du k retenu sont décrits (effectifs, médianes). Un seul
   motif de refus est admis : deux segments ne peuvent pas recevoir d'actions différentes.
   Dans ce cas, on passe au k admissible suivant dans l'ordre des sommes de rangs. Ce refus
   doit être écrit dans ce journal avec ses raisons métier (jamais une valeur d'indice), et
   poussé avant le calcul des indices externes.
5. **Si aucun k n'est admissible** : parmi les k qui respectent la condition (a), on retient
   celui dont l'ARI bootstrap moyen est le plus haut (égalité : le plus petit k), et on le dit
   clairement.
6. **Désaccords entre indices** : le rapport indique quel k chaque indice préfère et explique
   pourquoi ils divergent ; la décision reste celle de la règle.

### Règle qui ramène la note d'avis au client

La table des avis n'est chargée qu'après le choix de k, commité et poussé.

- Seuls comptent les avis des commandes retenues du client (livrées, achetées du 2017-01-01 au
  2018-06-30).
- **Une note par commande** : si une commande a plusieurs avis, on prend le plus récent (date
  de réponse, puis date de création, puis `review_id` par ordre alphabétique).
- **Note du client = moyenne des notes de ses commandes.** Pour 97 % des clients (une seule
  commande), c'est simplement la note de cette commande.
- **Étiquette principale : « satisfait » si la note du client vaut au moins 4**, « non
  satisfait » sinon (deux classes). Raison : c'est la mesure de satisfaction usuelle (les deux
  meilleures notes), plus robuste qu'une note à 5 niveaux pour un client à plusieurs commandes.
- **Clients sans avis** : exclus du calcul des indices externes (aucune valeur inventée) ; leur
  nombre et leur part dans chaque segment sont donnés.

### Évaluation externe (seulement après le choix de k)

- Indices calculés entre la partition retenue (64 805 clients d'apprentissage, clients sans
  avis exclus) et l'étiquette « satisfait » : **ARI, NMI, V-measure** (avec ses deux parts,
  homogénéité et complétude).
- **Par segment** : part de satisfaits, note moyenne, part de notes à 1, nombre de clients avec
  avis, part de clients sans avis.
- Les mêmes indices sont donnés pour les autres méthodes au même k, à titre de comparaison ;
  ils ne changent aucune décision.
- Attendu, écrit d'avance : avec une étiquette à deux classes et des segments de comportement,
  l'ARI et la NMI seront faibles par nature ; les taux par segment seront les plus parlants. Et
  les variables de délai, qui entrent dans le clustering, sont liées à la note : une partie du
  lien entre segments et satisfaction vient de là, ce qui sera dit.
- Les avis des 20 % mis de côté ne sont regardés qu'à la vérification finale.

### Paramètres de l'étape 5, fixés d'avance

- **Échantillon commun** : 8 000 clients d'apprentissage tirés avec la graine 42 (ordre aléatoire
  fixé). Il sert aux silhouettes de toutes les méthodes et de tous les k.
- **Échantillon de la CAH** : les 6 000 premiers clients de cet échantillon commun (échantillons
  emboîtés), pour la CAH de Ward, la CAH de la classification mixte et la corrélation
  cophénétique. **Mémoire mesurée** (le 2026-11-09, sur données aléatoires de même forme, pour
  ne calculer aucune partition avant le push de ces règles) : pic de **28 × n² octets**, soit
  **1,79 Go pour 8 000 clients** et 1,01 Go pour 6 000 (scipy fait des copies internes du
  tableau des distances ; une première estimation de 12 × n² octets, écrite dans le brouillon de
  cette entrée, était fausse). La mémoire libre, mesurée avec Chrome ouvert, a varié de 1,8 Go à
  6,7 Go dans la journée.
  **Règle fixe : l'échantillon de la CAH compte toujours 6 000 clients**, les 6 000 premiers de
  l'échantillon de 8 000 des silhouettes. Avant le calcul, le script mesure la mémoire libre ;
  **si elle est inférieure à 2,0 Go, il refuse de démarrer** avec un message clair (fermer des
  programmes et relancer), **sans changer la taille**. La mesure est écrite dans le rapport.
  Raisons :
  - **reproductibilité** : une taille qui dépendrait de la mémoire libre donnerait des résultats
    différents selon le PC et le moment ; avec une taille fixe, le même code donne toujours la
    même CAH ;
  - **6 000 plutôt que 8 000** : pic de 1,01 Go, soit la moitié des 2,0 Go exigés ; 8 000
    (1,79 Go) ne tiendrait pas dans la mémoire libre la plus basse observée (1,8 Go) ;
  - **la CAH sert seulement à comparer**, pas à décider k (la règle de k s'applique à K-Means sur
    les 64 805 clients) : un échantillon de 6 000 clients suffit pour le dendrogramme, la
    corrélation cophénétique et la comparaison avec K-Means. Pour la classification mixte, la
    CAH ne fournit que les centres de départ ; la consolidation par K-Means porte ensuite sur les
    64 805 clients.
- **K-Means** : initialisation k-means++, 20 initialisations, 300 itérations au plus, graine 42,
  sur les 64 805 clients et les 8 variables préparées.
- **CAH de Ward** : distance euclidienne, sur l'échantillon de la CAH et les 8 variables ;
  dendrogramme (30 dernières fusions) ; corrélation cophénétique.
- **Classification mixte** : CAH de Ward sur l'échantillon de la CAH, coordonnées F1–F5 non
  restandardisées ; coupe en k segments ; centres = moyennes des segments ; consolidation par
  K-Means (1 initialisation, à partir de ces centres) sur les 64 805 clients, dans l'espace
  F1–F5.
- **HDBSCAN** : sur les 64 805 clients, coordonnées F1–F5 ; taille minimale d'un groupe =
  1 297 clients (2 %, comme la taille minimale d'un segment) ; `min_samples` = 25 ; méthode de
  sélection par défaut (« eom »). Aucun réglage après coup. Si le calcul dépasse la mémoire ou
  30 minutes, il est refait sur l'échantillon commun de 8 000 clients (taille minimale 160,
  soit 2 %), et c'est écrit ici. La part de clients classés « bruit » est donnée.
- **Contrôle de sensibilité** : la classification mixte est refaite avec 4 axes (F1–F4) au lieu
  de 5, même échantillon, mêmes k. On mesure l'accord entre les deux partitions (ARI) pour
  chaque k. C'est une description : la décision de 5 axes ne change pas.
- **Tableau comparatif** : pour chaque méthode, au k retenu (et indices pour k de 2 à 8) :
  données utilisées, nombre de clients, nombre de segments, taille du plus petit segment, part
  de bruit, R², silhouette, Calinski-Harabasz et Davies-Bouldin **calculés dans le même espace
  (les 8 variables préparées, silhouette sur l'échantillon commun)** pour que les méthodes
  soient comparables, corrélation cophénétique (CAH), accord avec la méthode de référence (ARI),
  temps de calcul, mémoire, possibilité d'affecter un nouveau client, dépendance au choix du
  nombre d'axes.
- **Temps de calcul estimé** (mesuré le 2026-11-09 sur données aléatoires de même forme, sur ce
  PC, Chrome ouvert) : une initialisation de K-Means sur 64 805 × 8 prend de 0,04 s (k = 2) à
  0,16 s (k = 7), soit environ 0,6 s pour k = 2 à 8.
  - K-Means de référence, 20 initialisations, k = 2 à 8 : environ 12 s ;
  - **bootstrap** : 50 tirages × 7 valeurs de k × **10** initialisations (la règle fixe 10, et
    non 20, dans le bootstrap) = 3 500 initialisations, environ **5 minutes**, plus les
    affectations et les ARI/Jaccard (quelques secondes). Avec 20 initialisations, ce serait
    environ 10 minutes ;
  - CAH de Ward avec corrélation cophénétique : environ 1,5 s pour 6 000 clients (trois CAH :
    8 variables, F1–F5, et F1–F4 pour la sensibilité) ;
  - HDBSCAN : 0,5 s ; 1,7 s ; 6,5 s pour 8 000 ; 16 000 ; 32 000 points (temps environ
    multiplié par 3,5 à 4 quand n double), soit environ 25 s attendues pour 64 805 ;
  - silhouettes (échantillon de 8 000) : quelques secondes par partition, environ 1 minute
    en tout.
  **Total attendu : environ 7 minutes, jusqu'à 20 minutes** avec une marge d'un facteur 2 à 3,
  car les vraies données peuvent demander plus d'itérations que des données aléatoires. Le
  bootstrap en représente l'essentiel.

## 2026-11-09 – Étape 5 : résultats des partitions (avant application de la règle de k)

Paramètres appliqués sans modification (détail dans `reports/partitions.md` et
`reports/indices_partitions.csv`). Aucun avis chargé ; règle de k pas encore appliquée.

- **Mémoire** : 7,14 Go libres au démarrage (minimum exigé 2,0 Go) ; pic du calcul 1,50 Go.
- **Temps de calcul : 45 minutes, au lieu de 7 à 20 estimées.** Le bootstrap a pris 2 683 s à
  lui seul, en n'utilisant qu'un seul cœur sur 12 (mesuré pendant le calcul), alors qu'une
  initialisation de K-Means sur les vraies données prend environ 0,1 s. **Cause non étudiée** (choix
  de l'utilisateur, à voir plus tard). **Sans effet sur les résultats** : le calcul est
  déterministe (graines fixées), seul le temps est en cause. L'estimation de l'entrée précédente
  était donc fausse d'un facteur 9 environ.
- **K-Means sur les 8 variables (référence), k = 2 à 8** : silhouettes faibles partout (0,157 à
  0,201), comme attendu pour un nuage continu ; les indices ne préfèrent pas le même k
  (silhouette : k = 4, presque à égalité avec 5 ; Calinski-Harabasz : k = 6 ; Davies-Bouldin :
  k = 7). Stabilité : très forte pour k = 2, 6 et 7 (ARI minimum ≥ 0,93) ; k = 4 et 5 stables en
  moyenne mais avec des tirages très différents (ARI minimum 0,30 et 0,35).
- **Segment des clients qui recommandent** : dès k = 3, K-Means isole un segment de 2,98 % qui
  contient exactement les 1 931 clients d'apprentissage à plusieurs commandes, et eux seuls
  (Jaccard 1,00). La CAH, la classification mixte et HDBSCAN l'isolent aussi : c'est le groupe le
  plus net du jeu de données (effet de la Fréquence, anticipé à l'étape 3).
- **k = 2 (K-Means)** sépare les clients par la valeur de l'achat (médianes 148,90 R$ contre
  44,50 R$, 3 mensualités contre 1, part des frais de port 0,12 contre 0,27).
- **CAH de Ward (8 variables, 6 000)** : corrélation cophénétique 0,531 (l'arbre ne respecte que
  moyennement les distances) ; accord avec K-Means faible (ARI de 0,25 à 0,46).
- **Classification mixte F1–F5** : corrélation cophénétique 0,506 ; très proche de K-Means pour
  k = 3 à 5 (ARI 0,96 à 0,97), moins pour k = 6 à 8 (0,55 à 0,74). À k = 2, silhouette 0,498 :
  elle isole seulement les 3 % de clients qui recommandent ; une silhouette élevée ne signifie
  donc pas une segmentation utile.
- **Contrôle de sensibilité (mixte F1–F4 contre F1–F5)** : ARI de 0,50 à 0,72 pour k = 3 à 8
  (−0,01 pour k = 2). Sans F5 (réachat), le segment des clients qui recommandent disparaît (plus
  petit segment d'environ 11 %). La classification mixte dépend donc fortement du choix 4 ou
  5 axes, ce qui confirme la raison, écrite d'avance, de prendre K-Means sur les 8 variables
  comme référence. La décision de 5 axes ne change pas.
- **HDBSCAN (F1–F5)** : 3 groupes, 87,2 %, 8,4 % et 3,0 % (les clients qui recommandent), et
  1,4 % de bruit ; il confirme une grande masse continue et un petit groupe à part.
- **Mise en garde sur Calinski-Harabasz** : cet indice augmente avec le nombre de clients. La
  valeur de la CAH, calculée sur 6 000 clients (environ 1 000), n'est pas comparable aux valeurs
  calculées sur les 64 805 clients (environ 12 000). Silhouette, Davies-Bouldin et R² restent
  comparables entre méthodes.
- **Correction** : le titre du dendrogramme de la classification mixte n'affichait pas sa
  corrélation cophénétique (0,506) ; corrigé dans le code (le graphique sera à jour au prochain
  lancement).

## 2026-11-09 – Choix de k : k = 5 (règle appliquée sans modification)

Détail dans `reports/choix_k.md` (script `scripts/choisir_k.py`). Aucun avis chargé avant ce choix.

- **Admissibilité** : les 7 valeurs de k sont admissibles (plus petit segment ≥ 2 %, ARI
  bootstrap moyen ≥ 0,80, Jaccard moyen de chaque segment ≥ 0,60). Le plus juste est k = 4
  (ARI moyen 0,802368).
- **Rangs** (valeurs exactes recalculées à partir des étiquettes enregistrées) : sommes
  k = 2 : 21 ; k = 3 : 18 ; k = 4 : 10 ; **k = 5 : 7** ; k = 6 : 8 ; k = 7 : 8 ; k = 8 : 12.
  **k = 5 est retenu** : aucun indice ne le place premier (silhouette 2e, Calinski-Harabasz 2e,
  Davies-Bouldin 3e), mais il est le meilleur compromis. Désaccords entre indices : la silhouette
  préfère k = 4 (0,2007, contre 0,1996 pour k = 5), Calinski-Harabasz k = 6, Davies-Bouldin
  k = 7 ; avec un nuage continu, ces indices mesurent des choses différentes (séparation de
  chaque client, rapport entre dispersions, ressemblance des segments voisins) et n'ont pas de
  raison de converger.
- **Stabilité de k = 5, décrite honnêtement** : ARI bootstrap moyen 0,907 (recalculé :
  0,9074394414761894, identique à la valeur publiée, ce qui confirme la reproductibilité),
  médiane 0,982, minimum 0,345. Les 50 tirages se partagent en deux groupes, sans rien entre
  0,60 et 0,90 : **44 tirages** retrouvent presque exactement la partition (ARI ≥ 0,92), et
  **6 tirages** (ARI de 0,35 à 0,44) tombent sur une **découpe concurrente**. Les 6 découpes
  concurrentes se ressemblent entre elles (ARI de 0,69 à 0,95) : c'est en gros une seule autre
  façon de couper. Dans cette découpe concurrente, **S3 (achats de plusieurs articles) et S4
  (clients qui recommandent) sont inchangés** (98,7 % et 100 % de leurs clients restent
  ensemble) ; la grande masse S0–S1–S2 est recoupée en trois niveaux de valeur (environ 85 R$,
  160 R$ et 30 R$ médians) et **le segment S2 « Livraison lente ou en retard » disparaît**, ses
  clients se répartissant dans les trois autres. S2 est donc le segment le plus fragile
  (Jaccard moyen 0,90), même s'il ressort dans 44 tirages sur 50.
- **Critère métier (règle 4) : validé par l'utilisateur pour k = 5**, chaque segment recevant
  une action différente :
  - S0 « Gros achats en plusieurs fois » (40,2 % des clients, 57,0 % du chiffre d'affaires ;
    médianes 129,90 R$, 3 mensualités) : offres premium et paiement en plusieurs fois ;
  - S1 « Petits achats, livraison chère » (31,9 % ; 35,00 R$, frais de port = 29 % du prix) :
    livraison gratuite à partir d'un seuil, pour grossir le panier ;
  - S2 « Livraison lente ou en retard » (15,8 % ; délai médian 24,2 jours, 40,7 % de retards) :
    geste commercial et suivi de la logistique ;
  - S3 « Achats de plusieurs articles » (9,1 % ; 2 articles par commande) : lots et ventes
    croisées ;
  - S4 « Clients qui recommandent » (3,0 % ; tous les clients à plusieurs commandes) : programme
    de fidélité.
  Aucun refus métier : k = 5 est définitif.
- **Mises en garde** : S2 est défini par la livraison, il sera donc lié à la note d'avis par
  construction (un retard entraîne souvent une mauvaise note) ; S2 est aussi plus récent
  (Récence médiane 158 jours contre environ 200), les retards s'étant concentrés sur certains
  mois (février et mars 2018) : une partie de S2 tient à la période d'achat.
- **Segments enregistrés** dans `models/segments.json` : centres dans l'espace des 8 variables
  préparées (moyennes des segments), noms et actions. Réaffecter les clients d'apprentissage au
  centre le plus proche redonne leur segment pour 99,9475 % d'entre eux ; 34 clients (0,05 %)
  changeraient de segment, car K-Means s'arrête avant la convergence parfaite. La partition de
  référence (celle sur laquelle k a été choisi) reste la partition officielle des 80 % ; les
  nouveaux clients sont affectés avec les centres enregistrés.

## 2026-11-09 – Évaluation externe sur les 80 % (après le choix de k)

Règle appliquée sans modification ; avis chargés seulement après le push du choix de k ; **avis
des 20 % non lus** (filtrage aux commandes des clients d'apprentissage, arrêt automatique si un
client mis de côté apparaissait). Détail dans `reports/evaluation_externe.md`.

- **Couverture** : 64 374 clients d'apprentissage sur 64 805 ont au moins un avis ; 431
  (0,67 %) n'en ont pas et sont exclus des indices, sans valeur inventée. Leur part par segment
  va de 0,4 % (S4) à 1,3 % (S2) : pas de concentration gênante. 78,0 % des clients notés sont
  « satisfaits » (note ≥ 4).
- **Indices externes** (K-Means, k = 5, contre « satisfait ») : ARI 0,0669 ; NMI 0,0393 ;
  V-measure 0,0393 (homogénéité 0,0699, complétude 0,0274). Faibles, comme écrit d'avance : une
  étiquette à deux classes (78 % / 22 %) ne peut pas reproduire 5 segments de comportement.
  Les autres méthodes au même k donnent des valeurs du même ordre (ARI de 0,039 à 0,100) ; elles
  ne changent aucune décision.
- **Taux par segment** (le plus parlant) : satisfaits S0 85,7 % ; S1 84,0 % ; **S2 54,9 %** ;
  **S3 63,7 %** ; S4 74,1 % (ensemble : 78,0 %). Part de notes à 1 : S2 27,0 % ; S3 20,9 % ;
  autres segments de 4,3 % à 5,1 %.
- **S2 lié à la note par construction** (rappelé en tête du rapport) : les clients livrés en
  retard en moyenne sont 24,9 % de satisfaits (note moyenne 2,22) contre 82,0 % (4,27) pour les
  autres. La faible satisfaction de S2, défini par la livraison, ne prouve donc pas que la
  segmentation « découvre » la satisfaction.
- **S3 n'est pas lié à la note par construction**, et c'est le constat le plus intéressant :
  ses délais sont normaux (médiane 10,2 jours, 3,0 % de retards), et pourtant seuls 63,7 % de ses
  clients sont satisfaits, avec 20,9 % de notes à 1. Hypothèse, **non vérifiée** : les commandes
  de plusieurs articles peuvent être livrées en plusieurs fois ou être incomplètes. À présenter
  comme une piste, pas comme un résultat.
- **S4 (clients qui recommandent)** : 74,1 %, un peu sous la moyenne ; leur note est une moyenne
  sur plusieurs commandes, ce qui rend le seuil de 4 plus difficile à atteindre.

## 2026-11-09 – Segments officiels = centre le plus proche

- **Décision** : le segment officiel de chaque client d'apprentissage est désormais le centre le
  plus proche de `models/segments.json`, exactement comme l'API le fera pour un nouveau client
  (une seule règle d'affectation pour tout le projet). Les centres ne changent pas (moyennes de
  la partition K-Means sur laquelle k a été choisi). Fichiers : `segmentation/segments.py`,
  `data/processed/segments_apprentissage.csv` (non versionné), `reports/segments_officiels.md`.
- **34 clients changent de segment sur 64 805 (0,0525 %)**, comme attendu : 20 de S2 vers S0,
  10 de S2 vers S1, 3 de S1 vers S0, 1 de S0 vers S1 (tous à la frontière de S2) ; S3 et S4 ne
  changent pas.
- **Effet négligeable** : écart relatif maximal des médianes des 8 variables 0,098 % ; part du
  chiffre d'affaires modifiée de 0,04 point au plus (S0 56,97 % → 57,00 %) ; évaluation externe
  refaite avec les segments officiels : ARI 0,0669 → 0,0670, homogénéité 0,0699 → 0,0698, NMI et
  V-measure inchangées (0,0393), parts de satisfaits inchangées au dixième près, notes à 1 de S2
  27,0 % → 27,1 %.

## 2026-11-09 – Hypothèse sur S3 (description seulement)

Rien ne change dans la segmentation. Détail dans `reports/hypothese_s3.md` (clients
d'apprentissage avec avis ; avis des 20 % non lus). « Plusieurs vendeurs » = au moins une
commande retenue du client avec des articles de plusieurs vendeurs, donc probablement plusieurs
colis.

- **Dans S3** : 738 clients avec au moins une commande à plusieurs vendeurs, **39,2 % de
  satisfaits** (note moyenne 2,83 ; 36,7 % de notes à 1) ; 5 092 clients à un seul vendeur,
  **67,2 %** (3,76 ; 18,6 %). Écart −28,0 points, intervalle de confiance à 95 % [−31,8 ; −24,3].
- Critère de lecture fixé dans le script avant le calcul (non validé à l'avance par
  l'utilisateur) : écart « net » si au moins 10 points et intervalle entièrement sous 0.
  **L'écart est net : c'est une piste qui soutient l'hypothèse**, sans la prouver (comparaison
  descriptive ; d'autres différences entre ces clients peuvent jouer).
- **Ce que l'hypothèse n'explique pas** : même à un seul vendeur, les clients de S3 restent
  moins satisfaits (67,2 %) que ceux des autres segments à un seul vendeur (79,5 %). Les
  plusieurs vendeurs ne concernent que 12,7 % des clients de S3 : si ces clients étaient aussi
  satisfaits que les autres clients de S3, S3 passerait d'environ 63,7 % à environ 67,2 % de
  satisfaits ; ils n'expliquent donc qu'une partie de l'écart de S3 avec l'ensemble (78,0 %).
- **Hors de S3**, le même écart existe (−26,0 points, [−35,8 ; −16,3]), mais sur seulement 101
  clients : les commandes à plusieurs vendeurs sont presque toutes dans S3.
- **Piste pour l'action de S3** (« lots et ventes croisées ») : privilégier des lots d'un même
  vendeur, pour éviter les envois en plusieurs colis. À présenter comme une suggestion.

## 2026-11-09 – Étape 6 (module 5, explicabilité) : règles fixées avant tout calcul

Ces règles sont écrites, commitées et poussées avant tout calcul de l'étape 6. La règle de
non-retour s'applique. Les segments sont les segments officiels (centre le plus proche). Aucun
avis n'est utilisé dans cette étape.

### Profils des segments (sur les 80 %)

- **Indice de profil** = moyenne du segment / moyenne de tous les clients d'apprentissage, sur
  les variables en unités d'origine. Lecture : au moins 1,20 « nettement au-dessus », au plus
  0,80 « nettement en dessous ».
- **Exception fixée d'avance : l'écart à la date promise**, dont la moyenne est négative
  (environ −12 jours) : un rapport n'aurait pas de sens (un segment livré plus tard que la
  moyenne pourrait obtenir un rapport inférieur à 1). Pour cette variable, on donne la
  **différence en jours** (moyenne du segment − moyenne globale).
- **Part du chiffre d'affaires** = somme des prix des articles du segment / total (R$, frais de
  port non compris, comme le Montant). Avec aussi : effectif, part des clients, médianes des
  8 variables, et, pour décrire seulement, les 3 États les plus fréquents, le moyen de paiement
  principal et les 3 premières catégories de produits.

### Arbre de décision de substitution

- **Rôle** : expliquer les segments par des règles lisibles. Ce n'est **pas** le modèle
  d'affectation (qui reste le centre le plus proche).
- **Apprentissage** : sur les 64 805 clients d'apprentissage, cible = segment officiel,
  variables = les 8 variables en **unités d'origine** (le log et l'écrêtage conservent l'ordre
  des valeurs, donc des seuils sur les valeurs d'origine sont équivalents) ; critère de Gini ;
  graine 42 ; **au moins 649 clients par feuille** (1 % des clients d'apprentissage, arrondi au
  supérieur).
- **Fidélité** = part des clients pour lesquels l'arbre donne le segment officiel. Mesurée sur
  les 80 %, et sur les 20 % mis de côté (leurs 8 variables, préparées et affectées au centre le
  plus proche ; aucun avis lu). Aussi : fidélité par segment et tableau des confusions.
- **Règle de choix de la profondeur** : **profondeur 3 si sa fidélité sur les 80 % atteint au
  moins 90 % ; sinon profondeur 4 si elle gagne au moins 3 points de fidélité sur les 80 % ;
  sinon profondeur 3.** La décision se prend sur les 80 % seulement ; les 20 % servent à vérifier.
- **Règles en phrases** : chaque feuille devient une phrase ; les conditions portant sur une
  même variable sont regroupées (« entre … et … ») ; seuils arrondis à l'affichage (R$ et
  proportions à 2 décimales, jours et mensualités à 1 décimale) ; chaque phrase donne le
  segment majoritaire de la feuille, son effectif et sa pureté (part des clients de la feuille
  qui sont vraiment dans ce segment). Le modèle garde les seuils exacts.

### Explication d'un client

Dans l'espace des 8 variables préparées (étape 3) :

- **Segment** (centre le plus proche) et **distance au centre** de ce segment.
- **Client « à la frontière »** si la distance au centre de son segment vaut **au moins 90 % de
  la distance au 2e centre le plus proche**. La part de clients concernés sera donnée après le
  calcul (80 % et 20 %).
- **Deux explications, dans cet ordre** :
  1. **ce qui explique son segment** : les 3 variables qui l'éloignent le plus du **client
     moyen** (le centre global, c'est-à-dire 0 dans l'espace préparé, puisque la standardisation
     est apprise sur les 80 %) ; part de chaque variable = carré de sa coordonnée préparée /
     somme des carrés ;
  2. **ce qui explique s'il est atypique** : les 3 variables qui l'éloignent le plus du **centre
     de son segment** ; part de chaque variable = carré de l'écart au centre / carré de la
     distance au centre.
  Pour chaque variable citée : le sens (au-dessus ou en dessous), et les valeurs **en unités
  d'origine** : la valeur du client, la moyenne globale (80 %) et la médiane de son segment.
- **Client « atypique »** si sa distance au centre de son segment dépasse le **95e centile des
  distances des clients d'apprentissage de ce segment** (seuil propre à chaque segment, appris
  sur les 80 %). Par construction, environ 5 % des clients d'apprentissage de chaque segment
  sont atypiques ; sur les 20 %, on vérifie que cette part reste proche de 5 %.
- En complément : l'indicateur « écrêté à la préparation » (étape 3).

### Ce qui est enregistré

`models/explication.json` (texte, LF) : seuils « atypique » par segment, seuil de frontière
(0,90), moyennes globales et médianes des segments en unités d'origine, profondeur retenue,
fidélités, et règles de l'arbre en phrases. L'arbre lui-même est décrit dans ce fichier (seuils
exacts), pour que l'API n'ait pas besoin de scikit-learn.
