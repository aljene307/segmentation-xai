"""Contrôle qualité des tables Olist brutes ; écrit reports/qualite_donnees.md.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\controle_qualite.py
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation import qualite as q  # noqa: E402
from segmentation.donnees import charger_avis, charger_tables  # noqa: E402
from segmentation.telechargement import comparer_au_manifeste, inventaire  # noqa: E402

CLES = {
    "clients": ["customer_id"],
    "commandes": ["order_id"],
    "articles": ["order_id", "order_item_id"],
    "paiements": ["order_id", "payment_sequential"],
    "produits": ["product_id"],
    "vendeurs": ["seller_id"],
    "geolocalisation": None,
    "traduction_categories": ["product_category_name"],
}


def pic_memoire_mo() -> float | None:
    """Pic de mémoire vive du processus (Windows uniquement), en Mo."""
    if sys.platform != "win32":
        return None

    class Compteurs(ctypes.Structure):
        _fields_ = [("cb", ctypes.wintypes.DWORD), ("PageFaultCount", ctypes.wintypes.DWORD)]
        _fields_ += [(n, ctypes.c_size_t) for n in (
            "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
            "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

    processus = ctypes.windll.kernel32.GetCurrentProcess
    processus.restype = ctypes.wintypes.HANDLE  # poignée 64 bits, pas un entier 32 bits
    lire = ctypes.windll.psapi.GetProcessMemoryInfo
    lire.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(Compteurs), ctypes.wintypes.DWORD]
    lire.restype = ctypes.wintypes.BOOL
    c = Compteurs()
    c.cb = ctypes.sizeof(c)
    if not lire(processus(), ctypes.byref(c), c.cb):
        return None
    return c.PeakWorkingSetSize / 1024**2


def tableau(entetes: list[str], lignes: list[list]) -> str:
    def fmt(v):
        if isinstance(v, float):
            return f"{v:,.2f}".replace(",", " ")
        if isinstance(v, int):
            return f"{v:,}".replace(",", " ")
        return str(v)

    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    out += ["| " + " | ".join(fmt(v) for v in l) + " |" for l in lignes]
    return "\n".join(out)


def main() -> int:
    md: list[str] = ["# Contrôle qualité des données brutes Olist", ""]
    md.append("Rapport généré par `scripts/controle_qualite.py`. Comptes agrégés uniquement. "
              "Montants en réals brésiliens (R$).")

    # 1. Intégrité
    manifeste = json.loads(config.MANIFESTE.read_text(encoding="utf-8"))
    ecarts = comparer_au_manifeste(inventaire(config.DOSSIER_OLIST), manifeste)
    md += ["", "## 1. Intégrité des fichiers", "",
           f"Source : {manifeste['source']} — licence {manifeste['licence']}.",
           f"Comparaison au manifeste `docs/donnees_manifeste.json` : "
           f"{'identique' if not ecarts else 'ÉCARTS : ' + ', '.join(ecarts)}."]

    t = charger_tables()
    avis = charger_avis()

    # 2. Tables
    lignes = []
    for nom, df in t.items():
        r = q.resume_table(df, CLES[nom])
        lignes.append([nom, r["lignes"], r["colonnes"], r["doublons_exacts"],
                       r.get("cle", "—"), r.get("doublons_cle", "—")])
    r = q.resume_table(avis, ["review_id", "order_id"])
    lignes.append(["avis (à part)", r["lignes"], r["colonnes"], r["doublons_exacts"],
                   r["cle"], r["doublons_cle"]])
    md += ["", "## 2. Tables", "",
           tableau(["table", "lignes", "colonnes", "doublons exacts", "clé", "doublons de clé"],
                   lignes)]

    # 3. Manquants
    md += ["", "## 3. Valeurs manquantes", ""]
    for nom, df in list(t.items()) + [("avis (à part)", avis)]:
        m = q.manquants(df)
        if len(m):
            md += [f"**{nom}**", "",
                   tableau(["colonne", "manquants", "%"],
                           [[c, int(r.manquants), float(r.pct)] for c, r in m.iterrows()]), ""]
    sans = [n for n, df in t.items() if not len(q.manquants(df))]
    md.append(f"Aucune valeur manquante : {', '.join(sans)}.")

    # 4. Clés de jointure
    c, o, a, p = t["clients"], t["commandes"], t["articles"], t["paiements"]
    jointures = [
        ["commandes.customer_id absents de clients", q.orphelins(o["customer_id"], c["customer_id"])],
        ["clients.customer_id sans commande", q.sans_correspondance(c["customer_id"], o["customer_id"])],
        ["customer_id présents dans plusieurs commandes",
         int((o["customer_id"].value_counts() > 1).sum())],
        ["articles.order_id absents de commandes", q.orphelins(a["order_id"], o["order_id"])],
        ["commandes sans article", q.sans_correspondance(o["order_id"], a["order_id"])],
        ["articles.product_id absents de produits", q.orphelins(a["product_id"], t["produits"]["product_id"])],
        ["articles.seller_id absents de vendeurs", q.orphelins(a["seller_id"], t["vendeurs"]["seller_id"])],
        ["paiements.order_id absents de commandes", q.orphelins(p["order_id"], o["order_id"])],
        ["commandes sans paiement", q.sans_correspondance(o["order_id"], p["order_id"])],
    ]
    md += ["", "## 4. Clés de jointure", "", tableau(["contrôle", "nombre"], jointures)]

    # 5. Statuts
    statuts = o["order_status"].value_counts()
    md += ["", "## 5. Statuts de commande", "",
           tableau(["statut", "commandes", "%"],
                   [[s, int(n), round(100 * n / len(o), 2)] for s, n in statuts.items()])]

    # 6. Chronologie
    d = q.controles_dates(o)
    md += ["", "## 6. Chronologie des commandes", "",
           f"Achats du {d.pop('achat_min'):%Y-%m-%d} au {d.pop('achat_max'):%Y-%m-%d}.", "",
           tableau(["contrôle", "nombre"], [[k.replace("_", " "), v] for k, v in d.items()])]

    # 7. Montants
    m = q.controles_montants(a, p)
    desc = a[["price", "freight_value"]].describe().T
    md += ["", "## 7. Montants (R$)", "",
           tableau(["contrôle", "valeur"], [[k.replace("_", " "), v] for k, v in m.items()]), "",
           tableau(["variable (R$)", "min", "médiane", "moyenne", "max"],
                   [[i, float(r["min"]), float(r["50%"]), float(r["mean"]), float(r["max"])]
                    for i, r in desc.iterrows()]), "",
           tableau(["moyen de paiement", "lignes"],
                   [[k, int(v)] for k, v in p["payment_type"].value_counts().items()])]

    # 8. Clients
    n_cmd = q.commandes_par_client(c, o)
    rep = n_cmd.value_counts().sort_index()
    md += ["", "## 8. Clients : `customer_id` contre `customer_unique_id`", "",
           tableau(["mesure", "valeur"], [
               ["customer_id distincts", int(c["customer_id"].nunique())],
               ["customer_unique_id distincts (vrais clients)", int(c["customer_unique_id"].nunique())],
               ["clients avec 1 seule commande", int(rep.get(1, 0))],
               ["part des clients avec 1 seule commande (%)", round(100 * rep.get(1, 0) / rep.sum(), 2)],
               ["nombre maximal de commandes d'un client", int(n_cmd.max())],
           ]), "",
           tableau(["commandes par client", "clients"],
                   [[int(k), int(v)] for k, v in rep.items()])]

    # 9. Produits
    pr, tr = t["produits"], t["traduction_categories"]
    cats = pr["product_category_name"].dropna().unique()
    non_trad = sorted(set(cats) - set(tr["product_category_name"]))
    md += ["", "## 9. Produits", "",
           tableau(["mesure", "valeur"], [
               ["catégories distinctes", len(cats)],
               ["produits sans catégorie", int(pr["product_category_name"].isna().sum())],
               ["catégories sans traduction anglaise", len(non_trad)],
           ]), "",
           f"Catégories sans traduction : {', '.join(non_trad) or 'aucune'}."]

    # 10. Avis
    av = q.controles_avis(avis, o)
    notes = av.pop("repartition_notes")
    md += ["", "## 10. Avis (table tenue à l'écart, évaluation externe seulement)", "",
           tableau(["mesure", "valeur"], [[k.replace("_", " "), v] for k, v in av.items()]), "",
           tableau(["review_score", "avis", "%"],
                   [[int(k), int(v), round(100 * v / av["avis"], 2)] for k, v in notes.items()])]

    # 11. Mémoire
    pic = pic_memoire_mo()
    md += ["", "## 11. Mémoire", "",
           f"Pic de mémoire du contrôle (toutes tables chargées) : "
           f"{'non mesuré' if pic is None else f'{pic:,.0f} Mo'.replace(',', ' ')}."]

    sortie = config.DOSSIER_RAPPORTS / "qualite_donnees.md"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print(f"Rapport écrit : reports/qualite_donnees.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
