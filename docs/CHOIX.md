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
