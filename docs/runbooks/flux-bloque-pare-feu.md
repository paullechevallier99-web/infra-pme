# Un flux légitime est bloqué par le pare-feu

**Quand l'utiliser :** une communication prévue dans la matrice des flux échoue (délai dépassé), alors que le service tourne : une cible Prometheus `DOWN` avec `context deadline exceeded`, Traefik en `502`, une sauvegarde qui n'atteint pas Garage.
**Impact :** variable selon le flux.

## 1. Savoir quel pare-feu est concerné

| Le service visé est... | Filtré par |
|---|---|
| Un port **publié par Docker** (API 8000, Vaultwarden 8081, cAdvisor 8080, Grafana 3000, Prometheus 9090, Loki 3100, Traefik 443 et 8082) | La chaîne **DOCKER-USER** (`INFRA-DOCKER`) |
| SSH, node_exporter (9100), Garage (3900, 3903) | **UFW** |

## 2. Prouver que c'est le pare-feu

Sur la VM visée, le service répond-il **localement** ?

```
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:[port]/
```

Puis, pendant que la source réessaie, regarder les compteurs :

```
sudo iptables -L INFRA-DOCKER -v -n --line-numbers     # le compteur du DROP augmente ?
sudo journalctl -k -g "UFW BLOCK" --since "5 min ago" | tail -5
```

| Constat | Cause | Résolution |
|---|---|---|
| Le compteur du `DROP` augmente | La source n'est pas dans `docker_user_allowed` | Corriger la variable de la VM, redéployer |
| `UFW BLOCK` avec la source | Règle UFW absente | Corriger `firewall_rules` de la VM, redéployer |
| Rien ne bouge | Le paquet n'arrive pas : routage, VM source, ou service arrêté | Tester depuis la source avec `curl -v` ; vérifier le service |
| Service de filtrage inactif | `docker-user-filter` arrêté | `sudo systemctl status docker-user-filter` ; `start` |

## 3. Corriger dans le code, jamais à la main

Les règles sont générées par Ansible. Une règle ajoutée à la main disparaît au prochain déploiement :

```
cd ~/infra-pme/ansible
ansible-playbook playbooks/site.yml --limit [vm] --check --diff    # voir le changement
ansible-playbook playbooks/site.yml --limit [vm]
```

## 4. Retour arrière d'urgence

Si le filtrage bloque un service important et que la correction prend du temps :

```
sudo systemctl stop docker-user-filter
```

Les ports de Docker redeviennent joignables depuis tout le réseau : **solution temporaire**, à annuler dès la correction (`sudo systemctl start docker-user-filter`).

## Vérifier

Test avec témoin : la source autorisée répond `200`, une source interdite (la VM admin vers l'API, par exemple) reste bloquée.
