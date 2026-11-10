-- Migration 001 : classement des factures.
-- Idempotente : peut être rejouée à chaque déploiement sans effet de bord.
BEGIN;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version    TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE factures
    ADD COLUMN IF NOT EXISTS classement   TEXT,
    ADD COLUMN IF NOT EXISTS siret        CHAR(14),
    ADD COLUMN IF NOT EXISTS date_facture DATE,
    ADD COLUMN IF NOT EXISTS montant_ttc  NUMERIC(12, 2),
    ADD COLUMN IF NOT EXISTS numero       TEXT,
    ADD COLUMN IF NOT EXISTS chemin       TEXT;

CREATE INDEX IF NOT EXISTS factures_siret_date ON factures (siret, date_facture);
CREATE INDEX IF NOT EXISTS factures_classement ON factures (classement);

INSERT INTO schema_migrations (version) VALUES ('001_classement') ON CONFLICT DO NOTHING;

COMMIT;
