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
