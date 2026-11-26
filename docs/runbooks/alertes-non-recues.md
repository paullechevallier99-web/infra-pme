# Les alertes n'arrivent pas sur Discord

**Quand l'utiliser :** une panne est visible (dans Grafana ou Prometheus), mais aucun message n'arrive sur Discord ; ou un test d'alerte ne produit rien.
**Impact :** tu n'es plus prévenu, alors que la supervision fonctionne.

## 1. Remonter la chaîne

Une alerte passe par quatre étapes. Trouver la première qui ne se fait pas :

```
# 1. la règle est-elle déclenchée ? (pending, puis firing)
curl -s http://172.31.19.4:9090/api/v1/alerts | jq -r '.data.alerts[] | "\(.state)  \(.labels.alertname)"'
# 2. Prometheus parle-t-il à Alertmanager ?
curl -s http://172.31.19.4:9090/api/v1/alertmanagers | jq '.data.activeAlertmanagers'
# 3. Alertmanager a-t-il reçu l'alerte ?
ssh -i ~/.ssh/homelab ops@172.31.19.4 'sudo docker exec obs-alertmanager-1 amtool alert query --alertmanager.url=http://localhost:9093'
# 4. Alertmanager a-t-il réussi l'envoi ?
ssh -i ~/.ssh/homelab ops@172.31.19.4 'sudo docker logs --tail 30 obs-alertmanager-1'
```

| Constat | Cause | Résolution |
|---|---|---|
| Rien à l'étape 1 | La condition n'est pas remplie, ou pas encore assez longtemps (`for: 2m`) | Attendre ; vérifier l'expression de la règle |
| Étape 1 en `pending` | La durée `for` n'est pas encore écoulée | Normal pendant 2 minutes (InstanceDown, ServiceProbeFailed) |
| Liste vide à l'étape 2 | Prometheus ne joint pas Alertmanager | `sudo docker compose -f /opt/obs/compose.yml up -d alertmanager` |
| L'alerte n'apparaît pas à l'étape 3 | Silence en cours | `amtool silence query`, puis `amtool silence expire [id]` |
| Étape 4 : erreur `401`, `404` ou `invalid webhook` | Webhook Discord supprimé ou régénéré | Créer un webhook dans le salon (**Paramètres du salon**, **Intégrations**), le mettre dans `vault_discord_webhook`, déployer obs |
| Étape 4 : délai dépassé | obs ne sort pas vers Internet | Tester `curl -sI https://discord.com` depuis obs ; proxy ou réseau de l'école |
| Message reçu une fois, puis plus rien | Normal : regroupement, puis répétition toutes les 4 heures | Rien à faire |

## Vérifier

Test de bout en bout : arrêter Vaultwarden sur apps, attendre environ 3 minutes, constater le message `[FIRING]`, relancer, constater `[RESOLVED]`.

```
ssh -i ~/.ssh/homelab ops@172.31.19.3 'sudo docker compose -f /opt/apps/compose.yml stop vaultwarden'
ssh -i ~/.ssh/homelab ops@172.31.19.3 'sudo docker compose -f /opt/apps/compose.yml start vaultwarden'
```
