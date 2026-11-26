# Alerte InstanceDown

**Quand l'utiliser :** une cible de Prometheus ne répond plus depuis 2 minutes (`up == 0`).
**Gravité :** critique.
**Impact :** selon la cible : une VM entière, un agent de supervision, ou l'application.

## 1. Identifier la cible

Le message Discord indique `job` (le type de cible) et `instance` (adresse et port).

    curl -s http://172.31.19.4:9090/api/v1/targets | \
      jq -r '.data.activeTargets[] | select(.health=="down") | "\(.labels.job) \(.labels.host) \(.scrapeUrl) : \(.lastError)"'

| job | Ce qui ne répond plus |
|---|---|
| node | La VM entière, ou son node_exporter (port 9100) |
| cadvisor | L'agent des conteneurs (port 8080) |
| factures-api, factures-worker | L'application, sur apps |
| traefik | Les métriques de Traefik, sur edge |
| garage | Garage, sur backup |

## 2. La VM répond-elle ?

    ping -c 3 172.31.19.[X]
    ssh -i ~/.ssh/homelab ops@172.31.19.[X] uptime

| Résultat | Cause probable | Aller à |
|---|---|---|
| Pas de ping | VM éteinte ou bloquée | 3a |
| Ping, mais pas de SSH | SSH arrêté, réseau de la VM | 3b |
| SSH fonctionne | Seul un service ou un agent est arrêté | 3c |

## 3. Résoudre

**3a. VM éteinte.** Dans Proxmox, démarrer la VM. Si elle ne redémarre pas, ou si elle est
perdue : [reconstruire-une-vm.md](reconstruire-une-vm.md).

**3b. SSH injoignable.** Par la console Proxmox de la VM :

    sudo sshd -t                     # rien affiché = configuration valide
    sudo systemctl status ssh --no-pager | head -5
    ip -br a                         # la carte réseau a-t-elle son adresse ?

Corriger l'erreur affichée, puis `sudo sshd -t && sudo systemctl restart ssh`.

**3c. Un service ou un agent arrêté.** Sur la VM concernée :

    sudo docker ps -a --format "{{.Names}}  {{.Status}}"
    sudo docker compose -f /opt/agents/compose.yml logs --tail 30        # agents
    sudo docker compose -f /opt/apps/compose.yml logs --tail 30 api      # application

Relancer la stack concernée, par exemple : `sudo docker compose -f /opt/agents/compose.yml up -d`.
Si la cause est une modification manuelle : redéployer la VM depuis la VM admin
(`cd ~/infra-pme/ansible && ansible-playbook playbooks/site.yml --limit [vm]`).

**Cas particulier :** `context deadline exceeded` avec une VM qui fonctionne : le pare-feu bloque
Prometheus. Vérifier `sudo ufw status` et `sudo iptables -L INFRA-DOCKER -v -n` sur la VM.

## 4. Vérifier

    curl -s http://172.31.19.4:9090/api/v1/targets | jq -r '.data.activeTargets[].health' | sort | uniq -c

Toutes les cibles en `up`, et le message `[RESOLVED]` sur Discord.
