# Préparer et mener une maintenance

**Quand l'utiliser :** avant toute intervention volontaire qui peut couper un service : mise à jour majeure, reconstruction, changement de pare-feu, ouverture d'un accès temporaire.

## 1. Avant

```
cd ~/infra-pme && git pull && git status
make backup
ssh -i ~/.ssh/homelab ops@172.31.19.3 "sudo bash -c 'set -a; . /etc/restic/env; restic snapshots --latest 1'"   # noter l'identifiant
```

- Snapshot Proxmox des VM concernées (et de la VM admin si l'intervention la touche).
- Copie chiffrée de l'état Terraform si Terraform intervient.
- Prévenir les utilisateurs de la coupure.

## 2. Faire taire les alertes prévues

```
ssh -i ~/.ssh/homelab ops@172.31.19.4 "sudo docker exec obs-alertmanager-1 amtool silence add host=[vm] --duration=1h --comment='Maintenance' --alertmanager.url=http://localhost:9093"
```

Un silence suspend les **messages**, pas l'évaluation : les alertes restent visibles dans Grafana.

## 3. Pendant

Session tmux (une coupure SSH ne doit pas interrompre l'opération), une modification à la fois, et le plan Terraform ou `--check --diff` relu avant chaque application.

## 4. Après

```
cd ~/infra-pme/ansible && ansible-playbook playbooks/site.yml --check --diff | tail -5   # changed=0
cd ../terraform && terraform plan                                                     # No changes
```

- Lever le silence s'il court encore (`amtool silence expire [id]`).
- Vérifier les services et les cibles Prometheus.
- Supprimer les snapshots Proxmox devenus inutiles (ils occupent le stockage).
- Noter l'intervention : date, durée de coupure, ce qui a été changé.
