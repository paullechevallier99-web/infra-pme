import hashlib
import os
import time

import psycopg
import redis
from prometheus_client import Counter, Gauge, start_http_server

from worker.extraction import analyser_pdf

DB_DSN = os.environ["DATABASE_URL"]
STORAGE = os.environ.get("STORAGE_DIR", "/data")
# Délai de lecture (15 s) plus long que l'attente de brpop (5 s) :
# la bibliothèque n'abandonne jamais pendant une attente normale.
queue = redis.Redis.from_url(
    os.environ["REDIS_URL"], socket_timeout=15, health_check_interval=30
)

PROCESSED = Counter("factures_processed_total", "Factures traitées", ["status"])
CLASSEMENT = Counter("factures_classement_total", "Résultat du classement", ["resultat"])
QUEUE_LEN = Gauge("factures_queue_length", "Factures en attente de traitement")


def trouver_fichier(conn, fid: str) -> str:
    """Le fichier est à la racine au premier passage, puis dans son dossier de rangement."""
    racine = os.path.join(STORAGE, f"{fid}.pdf")
    if os.path.exists(racine):
        return racine
    row = conn.execute("SELECT chemin FROM factures WHERE id = %s", (fid,)).fetchone()
    if row and row[0]:
        return os.path.join(STORAGE, row[0])
    raise FileNotFoundError(f"fichier introuvable pour {fid}")


def process(fid: str) -> None:
    with psycopg.connect(DB_DSN, autocommit=True) as conn:
        source = trouver_fichier(conn, fid)
        with open(source, "rb") as f:
            data = f.read()
        r = analyser_pdf(data)

        # Rangement : classees/AAAA/MM/SIRET/<id>.pdf, ou a_verifier/<id>.pdf
        chemin = os.path.join(r.dossier(), f"{fid}.pdf")
        destination = os.path.join(STORAGE, chemin)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        if os.path.abspath(source) != os.path.abspath(destination):
            os.replace(source, destination)

        conn.execute(
            "UPDATE factures SET status = 'done', sha256 = %s, size_bytes = %s, processed_at = now(), "
            "classement = %s, siret = %s, date_facture = %s, montant_ttc = %s, numero = %s, chemin = %s "
            "WHERE id = %s",
            (hashlib.sha256(data).hexdigest(), len(data), r.classement, r.siret, r.date_facture,
             r.montant_ttc, r.numero, chemin, fid),
        )
    CLASSEMENT.labels(r.classement).inc()
    if r.manquants:
        print(f"{fid} à vérifier, informations manquantes : {', '.join(r.manquants)}", flush=True)

if __name__ == "__main__":
    start_http_server(9200)
    while True:
        try:
            QUEUE_LEN.set(queue.llen("factures:queue"))
            item = queue.brpop("factures:queue", timeout=5)
        except redis.exceptions.RedisError as exc:
            # Un incident Redis passager ne doit pas faire planter le worker
            print(f"Redis indisponible : {exc}, nouvelle tentative dans 5 s", flush=True)
            time.sleep(5)
            continue
        if item is None:
            continue
        fid = item[1].decode()
        try:
            process(fid)
            PROCESSED.labels("ok").inc()
        except Exception as exc:  # journalisé, compté, visible dans Grafana
            PROCESSED.labels("error").inc()
            print(f"erreur sur {fid}: {exc}", flush=True)
