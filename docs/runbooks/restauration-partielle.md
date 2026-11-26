# Restaurer une partie des données seulement

**Quand l'utiliser :** une facture supprimée par erreur, une base corrompue, un coffre Vaultwarden abîmé, sans que la VM apps soit perdue.
**Impact :** limité à ce qui est restauré. Pour une perte complète de apps : [restauration.md](restauration.md) et [reconstruire-une-vm.md](reconstruire-une-vm.md).

Toutes les commandes se tapent **sur apps** (`ssh -i ~/.ssh/homelab ops@172.31.19.3`), avec les identifiants de restic chargés :

```
sudo -i
set -a; . /etc/restic/env; set +a
```

## 1. Choisir le bon snapshot

```
restic snapshots
```

Prendre celui qui **précède** l'incident, en lisant sa date. Jamais `latest` sans vérifier : la dernière sauvegarde peut déjà contenir la perte.

## 2. Une facture (un fichier)

```
restic ls [ID] | grep [début de l'identifiant de la facture]
restic restore [ID] --target /tmp/restaure --include "[chemin affiché]"
cp /tmp/restaure/srv/factures/[chemin relatif] /srv/factures/[même chemin]
chown 10001 /srv/factures/[même chemin]
rm -rf /tmp/restaure
```

La ligne de la facture doit aussi exister en base : si elle a été supprimée, restaurer la base (point 3), ou réanalyser la facture.

## 3. La base PostgreSQL seule

```
restic restore [ID] --target /tmp/restaure --include /var/backups/staging/factures.dump
cd /opt/apps
docker compose stop api worker
docker compose exec -T postgres pg_restore -U factures -d factures --clean --if-exists --no-owner < /tmp/restaure/var/backups/staging/factures.dump
docker compose start api worker
rm -rf /tmp/restaure
```

## 4. Vaultwarden seul

```
restic restore [ID] --target /tmp/restaure --include /var/backups/staging/vaultwarden.sqlite3
sqlite3 /tmp/restaure/var/backups/staging/vaultwarden.sqlite3 "PRAGMA integrity_check;"   # doit répondre ok
cd /opt/apps && docker compose stop vaultwarden
cp /srv/vaultwarden/db.sqlite3 /srv/vaultwarden/db.sqlite3.avant-restauration
rm -f /srv/vaultwarden/db.sqlite3-wal /srv/vaultwarden/db.sqlite3-shm
cp /tmp/restaure/var/backups/staging/vaultwarden.sqlite3 /srv/vaultwarden/db.sqlite3
docker compose start vaultwarden
rm -rf /tmp/restaure
```

Les mots de passe ajoutés après le snapshot sont perdus : prévenir les utilisateurs, qui peuvent les ressaisir depuis le cache de leur application Bitwarden.

## Vérifier

```
curl -s https://factures.lab.internal/healthz              # depuis la VM admin
curl -s -o /dev/null -w "%{http_code}\n" https://vault.lab.internal/alive
```

## Après

Lancer une sauvegarde (`make backup`) pour figer l'état réparé, et noter l'incident.
