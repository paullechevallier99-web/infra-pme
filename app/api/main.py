import os
import re
import uuid

import psycopg
import redis
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from prometheus_client import Counter, Histogram, make_asgi_app

DB_DSN = os.environ["DATABASE_URL"]
STORAGE = os.environ.get("STORAGE_DIR", "/data")
MAX_SIZE = 10 * 1024 * 1024
queue = redis.Redis.from_url(os.environ["REDIS_URL"])

UPLOADS = Counter("factures_uploads_total", "Factures reçues", ["status"])
LATENCY = Histogram("factures_upload_seconds", "Durée de traitement d'un dépôt")

CHAMPS = ["id", "filename", "status", "sha256", "size_bytes", "classement", "siret",
          "date_facture", "montant_ttc", "numero", "chemin", "created_at"]
COLONNES = ", ".join(CHAMPS)

app = FastAPI(title="factures-api")
app.mount("/metrics", make_asgi_app())


def db():
    return psycopg.connect(DB_DSN, autocommit=True)


@app.get("/healthz")
def healthz():
    with db() as conn:
        conn.execute("SELECT 1")
    queue.ping()
    return {"status": "ok"}


@app.post("/factures", status_code=202)
async def upload(file: UploadFile = File(...)):
    with LATENCY.time():
        data = await file.read()
        if not data.startswith(b"%PDF") or len(data) > MAX_SIZE:
            UPLOADS.labels("rejected").inc()
            raise HTTPException(400, "PDF invalide ou trop volumineux")
        fid = str(uuid.uuid4())
        with open(os.path.join(STORAGE, f"{fid}.pdf"), "wb") as f:
            f.write(data)
        with db() as conn:
            conn.execute(
                "INSERT INTO factures (id, filename, status) VALUES (%s, %s, 'pending')",
                (fid, file.filename),
            )
        queue.lpush("factures:queue", fid)
        UPLOADS.labels("accepted").inc()
        return {"id": fid, "status": "pending"}


@app.get("/factures")
def rechercher(
    mois: str | None = Query(None, description="AAAA-MM"),
    siret: str | None = Query(None, min_length=14, max_length=14),
    classement: str | None = Query(None, pattern="^(classee|a_verifier)$"),
    limit: int = Query(50, ge=1, le=200),
):
    conditions, params = [], []
    if mois:
        if not re.fullmatch(r"\d{4}-\d{2}", mois):
            raise HTTPException(400, "mois attendu au format AAAA-MM")
        conditions.append("to_char(date_facture, 'YYYY-MM') = %s")
        params.append(mois)
    if siret:
        conditions.append("siret = %s")
        params.append(siret)
    if classement:
        conditions.append("classement = %s")
        params.append(classement)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with db() as conn:
        rows = conn.execute(
            f"SELECT {COLONNES} FROM factures {where} ORDER BY date_facture DESC NULLS LAST, "
            f"created_at DESC LIMIT %s",
            (*params, limit),
        ).fetchall()
    return [dict(zip(CHAMPS, row)) for row in rows]


@app.get("/factures/{fid}")
def get_facture(fid: uuid.UUID):
    with db() as conn:
        row = conn.execute(f"SELECT {COLONNES} FROM factures WHERE id = %s", (fid,)).fetchone()
    if row is None:
        raise HTTPException(404, "Facture inconnue")
    return dict(zip(CHAMPS, row))


@app.post("/factures/{fid}/reanalyser", status_code=202)
def reanalyser(fid: uuid.UUID):
    """Remet une facture dans la file : utile pour les factures déposées avant le classement."""
    with db() as conn:
        if conn.execute("SELECT 1 FROM factures WHERE id = %s", (fid,)).fetchone() is None:
            raise HTTPException(404, "Facture inconnue")
    queue.lpush("factures:queue", str(fid))
    return {"id": str(fid), "status": "requeued"}
