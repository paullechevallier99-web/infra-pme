# La supervision est hors service

**Quand l'utiliser :** Grafana ne s'ouvre plus, Prometheus ne répond pas, ou la VM obs est injoignable.
**Impact :** les services du cabinet fonctionnent, mais **tu n'es plus prévenu** d'une panne. Aucune alerte ne signale cette situation : c'est la limite connue (un système ne peut pas signaler sa propre panne).

## 1. Quelle brique est touchée ?

Depuis la VM admin :

```
ping -c 2 172.31.19.4
curl -s http://172.31.19.4:9090/-/healthy; echo
curl -s -o /dev/null -w "grafana : %{http_code}\n" https://grafana.lab.internal/api/health
ssh -i ~/.ssh/homelab ops@172.31.19.4 'sudo docker compose -f /opt/obs/compose.yml ps'
```

| Constat | Conséquence | Résolution |
|---|---|---|
| obs ne répond pas au ping | Toute la supervision est arrêtée | [vm-ne-demarre-pas.md](vm-ne-demarre-pas.md) ; obs se reconstruit sans données à restaurer ([reconstruire-une-vm.md](reconstruire-une-vm.md)) |
| Prometheus arrêté | Plus de métriques ni d'alertes | `sudo docker compose -f /opt/obs/compose.yml up -d prometheus`, puis ses journaux |
| Alertmanager arrêté | Les alertes se déclenchent mais ne partent pas | [alertes-non-recues.md](alertes-non-recues.md) |
| Grafana arrêté | Plus d'affichage ; les alertes partent quand même | `up -d grafana` ; mot de passe : [gerer-les-comptes.md](gerer-les-comptes.md) |
| Loki arrêté | Les journaux ne sont plus centralisés (ils restent sur chaque VM) | `up -d loki` ; disque d'obs : [disque-plein.md](disque-plein.md) |

## 2. Prometheus redémarre en boucle

```
ssh -i ~/.ssh/homelab ops@172.31.19.4 'sudo docker logs --tail 30 obs-prometheus-1'
```

| Message | Cause | Résolution |
|---|---|---|
| Erreur dans `prometheus.yml` ou dans un fichier de règles | Modification manuelle ou règle invalide | Redéployer obs ; valider les règles avec `promtool` (`make lint` ou la CI) |
| `no space left on device` | Disque plein | [disque-plein.md](disque-plein.md) |
| Données corrompues après un arrêt brutal | Base de séries temporelles abîmée | Supprimer le volume des données de Prometheus (l'historique de 15 jours est perdu, sans gravité), puis `up -d` |

## Vérifier

```
curl -s http://172.31.19.4:9090/api/v1/targets | jq -r '.data.activeTargets[].health' | sort | uniq -c
```

Une quinzaine de cibles `up`. Dans Grafana, les tableaux de bord se remplissent.

## Après

Le trou dans les métriques correspond à la panne. L'amélioration qui l'aurait signalée : un signal de vie (*dead man's switch*) envoyé en permanence vers un service extérieur, qui prévient quand il cesse.
