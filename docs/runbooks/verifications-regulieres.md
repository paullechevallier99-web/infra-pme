# Les vérifications régulières

**Quand l'utiliser :** au début d'une séance, chaque semaine, ou avant une démonstration. Aucune de ces commandes ne modifie l'infrastructure.

## Chaque séance (2 minutes)

```
cd ~/infra-pme && git pull && git status
cd ansible && ansible all -m ansible.builtin.ping
curl -s https://factures.lab.internal/healthz; echo
curl -s http://172.31.19.4:9090/api/v1/alerts | jq -r '.data.alerts[] | "\(.state)  \(.labels.alertname)"'
```

Attendu : dépôt à jour et propre, `pong` x4, `{"status":"ok"}`, aucune alerte.

## Chaque semaine (10 minutes)

| Vérification | Commande | Attendu |
|---|---|---|
| Cibles de supervision | `curl -s http://172.31.19.4:9090/api/v1/targets \| jq -r '.data.activeTargets[].health' \| sort \| uniq -c` | Une quinzaine de `up` |
| Sauvegarde de la nuit | `ssh ... ops@172.31.19.3 "sudo bash -c 'set -a; . /etc/restic/env; restic snapshots --latest 2'"` | Un snapshot de moins de 24 h |
| Test de restauration du dimanche | `ssh ... ops@172.31.19.3 'sudo journalctl -u restic-restore-test.service -n 3 --no-pager'` | « Restauration valide » |
| Dérive | `ansible-playbook playbooks/site.yml --check --diff \| tail -5` | `changed=0` |
| Terraform | `terraform plan` | No changes |
| Espace disque | `ansible all -m ansible.builtin.command -a "df -h /"` | Plus de 15 % libres partout |
| Certificat | `openssl x509 -in ~/infra-pme/pki/wildcard.crt -noout -enddate` | Plus de 21 jours |
| Propositions de Renovate | GitHub, onglet **Pull requests** | Traitées ou planifiées |
| CI | GitHub, onglet **Actions** | Dernière exécution verte |

## Avant une démonstration

Les vérifications de la séance, plus : déposer deux ou trois factures (pour remplir les tableaux de bord de Grafana), et vérifier l'accès depuis le poste qui servira à présenter (proxy ou route Tailscale, CA installée).
