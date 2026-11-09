"""API FastAPI de segmentation explicable des clients Olist (module 6).

Lancement local (depuis la racine du projet) :
    .venv\\Scripts\\python -m uvicorn api.main:app --port 8000
Documentation interactive : http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.moteur import Moteur
from api.schemas import CONTRAINTES, Client, Lot

VERSION = "1.1.0"
moteur = Moteur()
app = FastAPI(
    title="Segmentation explicable – clients Olist",
    version=VERSION,
    description="Affecte un client à l'un des 5 segments, l'explique et décrit les segments. "
                "Données : Brazilian E-Commerce Public Dataset by Olist (CC BY-NC-SA 4.0). "
                "Montants en réals brésiliens (R$).",
)


def _nombre(v) -> str:
    return str(v).replace(".", ",") if isinstance(v, (int, float)) else repr(v)


LOT_MAX = 1000


def traduire(erreurs_pydantic) -> list[dict]:
    """Erreurs de validation pydantic → liste {champ, message} en français."""
    erreurs = []
    for e in erreurs_pydantic:
        champ = str(e["loc"][-1]) if e["loc"] else "corps"
        t = e["type"]
        if t == "missing":
            msg = "valeur manquante"
        elif t == "extra_forbidden":
            msg = "champ inconnu (attendus : " + ", ".join(CONTRAINTES) + ")"
        elif t in ("finite_number",):
            msg = "nombre fini attendu (ni NaN ni infini)"
        elif t in ("float_parsing", "float_type", "int_parsing", "int_type"):
            msg = "nombre attendu" if "float" in t else "nombre entier attendu"
        elif t == "int_from_float":
            msg = "nombre entier attendu"
        elif t == "too_long" and champ == "clients":
            msg = f"au plus {LOT_MAX:,} clients par lot".replace(",", " ")
        elif t == "too_short" and champ == "clients":
            msg = "au moins 1 client attendu"
        elif champ in CONTRAINTES:
            msg = CONTRAINTES[champ]
        elif t in ("model_attributes_type", "model_type", "dict_type", "json_invalid"):
            champ, msg = "corps", "un objet JSON avec les 8 variables est attendu"
        elif t == "list_type":
            msg = "une liste de clients est attendue"
        else:
            msg = e.get("msg", "valeur invalide")
        if ("input" in e and t not in ("missing", "extra_forbidden", "too_long", "too_short")
                and champ != "corps"):
            msg += f", reçu {_nombre(e['input'])}"
        erreurs.append({"champ": champ, "message": msg})
    return erreurs


@app.exception_handler(RequestValidationError)
async def erreurs_en_francais(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Données invalides",
                                                  "erreurs": traduire(exc.errors())})


def memoire_processus() -> dict:
    """Mémoire du processus en Mo (actuelle et pic), lue dans /proc/self/status (Linux)."""
    try:
        lignes = Path("/proc/self/status").read_text().splitlines()
    except OSError:
        return {"actuelle_mo": "non disponible", "pic_mo": "non disponible"}
    valeurs = {l.split(":")[0]: l.split(":")[1].split()[0] for l in lignes
               if l.startswith(("VmRSS:", "VmHWM:"))}
    vers_mo = lambda k: round(int(valeurs[k]) / 1024, 1) if k in valeurs else "non disponible"  # noqa
    return {"actuelle_mo": vers_mo("VmRSS"), "pic_mo": vers_mo("VmHWM")}


@app.get("/health")
def sante() -> dict:
    return {"statut": "ok", "version": VERSION, "k": moteur.segments["k"],
            "modeles": {f: h[:12] for f, h in moteur.empreintes.items()},
            "memoire": memoire_processus()}


@app.get("/segments")
def segments() -> list[dict]:
    return moteur.decrire()


@app.get("/segments/{identifiant}")
def segment(identifiant: int) -> dict:
    tous = moteur.decrire()
    if not 0 <= identifiant < len(tous):
        raise HTTPException(404, f"segment {identifiant} inconnu (0 à {len(tous) - 1})")
    return tous[identifiant]


@app.get("/regles")
def regles() -> dict:
    a = moteur.expl["arbre"]
    return {"profondeur": a["profondeur"], "fidelite_80": a["fidelite_80"],
            "fidelite_20": a["fidelite_20"], "phrases": moteur.expl["regles"],
            "remarque": "S4 « Clients qui recommandent » est exactement l'ensemble des clients à "
                        "au moins 2 commandes (100 %) ; l'arbre ne le retrouve qu'à 71,7 %, car il "
                        "cherche la meilleure fidélité globale."}


@app.post("/affecter")
def affecter(client: Client) -> dict:
    import pandas as pd

    s = int(moteur.affecter(pd.DataFrame([client.model_dump()]))[0])
    return moteur.segment(s)


@app.post("/expliquer")
def expliquer(client: Client) -> dict:
    return moteur.expliquer(client.model_dump())


@app.post("/affecter/lot")
def affecter_lot(lot: Lot) -> dict:
    """Jusqu'à 1 000 clients ; chaque ligne est validée séparément : une ligne invalide ne
    bloque pas les autres. Les lignes sont numérotées à partir de 1."""
    import pandas as pd

    resultats, valides, positions = [], [], []
    for i, brut in enumerate(lot.clients, start=1):
        try:
            valides.append(Client.model_validate(brut).model_dump())
            positions.append(len(resultats))
            resultats.append({"ligne": i})
        except ValidationError as exc:
            resultats.append({"ligne": i, "erreurs": traduire(exc.errors())})
    if valides:
        segs = moteur.affecter(pd.DataFrame(valides))
        for pos, s in zip(positions, segs):
            resultats[pos]["segment"] = moteur.segment(int(s))
    return {"total": len(resultats), "valides": len(valides),
            "invalides": len(resultats) - len(valides), "resultats": resultats}


@app.get("/exemples")
def exemples() -> list[dict]:
    return moteur.exemples
