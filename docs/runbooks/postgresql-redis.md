# PostgreSQL ou Redis ne fonctionne plus

**Quand l'utiliser :** l'API des factures répond en erreur, `/healthz` échoue, ou les journaux de l'API et du worker parlent de connexion à la base ou à Redis.
**Impact :** plus de dépôt ni de consultation de factures. Vaultwarden n'est pas concerné (il a sa propre base SQLite).

## 1. État des conteneurs

Sur apps :

```
cd /opt/apps
sudo docker compose ps postgres redis api worker
sudo docker compose logs --tail 40 postgres
sudo docker compose logs --tail 40 redis
```

| Constat | Cause | Résolution |
|---|---|---|
| `postgres` en `Restarting`, « No space left on device » | Disque plein | [disque-plein.md](disque-plein.md), puis `sudo docker compose up -d` |
| `postgres` en `Restarting`, erreur d'authentification | Mot de passe changé dans le coffre, mais base créée avec l'ancien | PostgreSQL ne lit son mot de passe qu'à la création : remettre l'ancien, ou le changer dans la base (`ALTER USER factures PASSWORD '...'`), puis redéployer |
| `postgres` `unhealthy` | La base démarre ou est surchargée | Attendre une minute ; sinon voir les journaux |
| Journaux : base corrompue | Arrêt brutal, disque abîmé | [restauration-partielle.md](restauration-partielle.md), point 3 |
| `redis` arrêté | Mémoire (limite 128 Mo) ou disque | `sudo docker compose up -d redis` ; voir [memoire-et-conteneurs.md](memoire-et-conteneurs.md) |
| Tout `Up`, mais l'API échoue | Mauvaise adresse ou mot de passe dans l'environnement de l'API | Redéployer apps : `ansible-playbook playbooks/site.yml --limit apps` |

## 2. Tester la base et la file directement

```
sudo docker compose exec postgres pg_isready -U factures
sudo docker compose exec postgres psql -U factures -d factures -c "SELECT count(*), status FROM factures GROUP BY status;"
sudo docker compose exec redis redis-cli ping
sudo docker compose exec redis redis-cli llen factures:queue
```

Attendu : `accepting connections`, des comptes par statut, `PONG`, et la longueur de la file (souvent 0).

## 3. Relancer proprement

```
sudo docker compose up -d
```

L'API attend que PostgreSQL soit `healthy` avant de démarrer.

## Vérifier

Depuis la VM admin : `curl -s https://factures.lab.internal/healthz` répond `{"status":"ok"}`.

## Après

Si des factures sont restées `pending` pendant la panne, elles sont dans la file Redis et seront traitées ; celles prises par un worker qui a planté restent `pending` (limite connue) : les réanalyser depuis la bibliothèque.
