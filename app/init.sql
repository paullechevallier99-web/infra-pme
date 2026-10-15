CREATE TABLE IF NOT EXISTS factures (
	id UUID PRIMARY KEY,
	filename TEXT NOT NULL,
	status TEXT NOT NULL,
	sha256 TEXT,
	size_bytes BIGINT,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
	processed_at TIMESTAMPTZ
);
