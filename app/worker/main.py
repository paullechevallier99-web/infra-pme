import hashlib
import os
import psycopg
import redis
from prometheus_client import Counter, Gauge, start_http_server

DB_DSN = os.environ["DATABASE_URL"]
STORAGE = os.environ.get("STORAGE_DIR", "/data")
queue = redis.Redis.from_url(os.environ["REDIS_URL"])

PROCESSED = Counter("factures_processed_total", "Factures traitées", ["status"])
QUEUE_LEN = Gauge("factures_queue_length", "Factures en attente de traitement")

def process(fid: str) -> None:
	with open(os.path.join(STORAGE, f"{fid}.pdf"), "rb") as f:
		data = f.read()
	with psycopg.connect(DB_DSN, autocommit=True) as conn:
		conn.execute(
			"UPDATE factures SET status = 'done', sha256 = %s, size_bytes = %s, "
			"processed_at = now() WHERE id = %s",
			(hashlib.sha256(data).hexdigest(), len(data), fid),
		)

if __name__ == "__main__":
	start_http_server(9200)
	while True:
		QUEUE_LEN.set(queue.llen("factures:queue"))
		item = queue.brpop("factures:queue", timeout=5)
		if item is None:
			continue
		fid = item[1].decode()
		try:
			process(fid)
			PROCESSED.labels("ok").inc()
		except Exception as exc: # journalisé, compté, visible dans Grafana
			PROCESSED.labels("error").inc()
			print(f"erreur sur {fid}: {exc}", flush=True)
