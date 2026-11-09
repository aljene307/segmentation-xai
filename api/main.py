"""API FastAPI de segmentation explicable des clients Olist (module 6).

Lancement local (depuis la racine du projet) :
    .venv\\Scripts\\python -m uvicorn api.main:app --port 8000
Documentation interactive : http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.moteur import Moteur
from api.schemas import CONTRAINTES, Client

VERSION = "1.0.0"
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


@app.exception_handler(RequestValidationError)
async def erreurs_en_francais(_: Request, exc: RequestValidationError) -> JSONResponse:
    erreurs = []
    for e in exc.errors():
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
        elif champ in CONTRAINTES:
            msg = CONTRAINTES[champ]
        elif t in ("model_attributes_type", "dict_type", "json_invalid"):
            champ, msg = "corps", "un objet JSON avec les 8 variables est attendu"
        else:
            msg = e.get("msg", "valeur invalide")
        if "input" in e and t not in ("missing", "extra_forbidden") and champ != "corps":
            msg += f", reçu {_nombre(e['input'])}"
        erreurs.append({"champ": champ, "message": msg})
    return JSONResponse(status_code=422, content={"detail": "Données invalides",
                                                  "erreurs": erreurs})


@app.get("/health")
def sante() -> dict:
    return {"statut": "ok", "version": VERSION, "k": moteur.segments["k"],
            "modeles": {f: h[:12] for f, h in moteur.empreintes.items()}}


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


@app.get("/exemples")
def exemples() -> list[dict]:
    return moteur.exemples
