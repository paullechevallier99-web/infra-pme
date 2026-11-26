# Alerte ServiceProbeFailed

**Quand l'utiliser :** un site (bibliothèque des factures, Vaultwarden, Grafana) ne répond plus
en HTTPS depuis 2 minutes. La sonde teste comme un utilisateur, à travers Traefik.
**Gravité :** critique.
**Impact :** les utilisateurs ne peuvent plus utiliser le service, même si la VM fonctionne.

## 1. Reproduire

Depuis la VM admin :

    curl -sv https://[service].lab.internal/ 2>&1 | grep -E "Connected|SSL|HTTP/"

| Résultat | Maillon en cause | Aller à |
|---|---|---|
| Pas de connexion à 172.31.19.2 | edge ou Traefik | 2a |
| Erreur de certificat | Certificat expiré ou mauvais | 2b |
| 404 | Route Traefik | 2c |
| 502 ou 504 | Le service derrière Traefik | 2d |

## 2. Résoudre

**2a. Traefik.** Sur edge :

    sudo docker ps --format "{{.Names}}  {{.Status}}" | grep traefik
    sudo docker logs --tail 30 edge-traefik-1

Relancer : `sudo docker compose -f /opt/edge/compose.yml up -d`.

**2b. Certificat.** [renouveler-certificat.md](renouveler-certificat.md).

**2c. Route absente.** Sur edge : `sudo cat /opt/edge/dynamic/routes.yml`. Redéployer edge si
le fichier diffère du dépôt (`ansible-playbook playbooks/site.yml --limit edge`).

**2d. Service arrêté.** Traefik répond mais ne joint pas le service. Sur apps (ou obs pour Grafana) :

    sudo docker compose -f /opt/apps/compose.yml ps
    sudo docker compose -f /opt/apps/compose.yml logs --tail 50 [vaultwarden|api]

Relancer le service : `sudo docker compose -f /opt/apps/compose.yml up -d`.
Si les conteneurs tournent : vérifier que le filtrage accepte edge
(`sudo iptables -L INFRA-DOCKER -v -n`).

## 3. Vérifier

    curl -s https://factures.lab.internal/healthz; echo
    curl -s -o /dev/null -w "%{http_code}\n" https://vault.lab.internal/alive
    curl -s -o /dev/null -w "%{http_code}\n" https://grafana.lab.internal/api/health

`{"status":"ok"}`, `200`, `200`, puis `[RESOLVED]` sur Discord.
