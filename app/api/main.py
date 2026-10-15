import os
import uuid
import psycopg
import redis
from fastapi import FastAPI, File, HTTPException, UploadFile
from prometheus_client import Counter, Histogram, make_asgi_app

DB_DSN = os.environ["DATABASE_URL"]
STORAGE = os.environ.get("STORAGE_DIR", "/data")
MAX_SIZE = 10 * 1024 * 1024
queue = redis.Redis.from_url(os.environ["REDIS_URL"])

UPLOADS = Counter("factures_uploads_total", "Factures reçues", ["status"])
LATENCY = Histogram("factures_upload_seconds", "Durée de traitement d'un dépôt")

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

@app.get("/factures/{fid}")
def get_facture(fid: uuid.UUID):
	with db() as conn:
		row = conn.execute(
			"SELECT id, filename, status, sha256, size_bytes FROM factures WHERE id = %s",
			(fid,),
		).fetchone()
	if row is None:
		raise HTTPException(404, "Facture inconnue")
	return dict(zip(["id", "filename", "status", "sha256", "size_bytes"], row))
