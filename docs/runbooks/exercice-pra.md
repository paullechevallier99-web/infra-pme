# Mener un exercice de reprise après sinistre

**Quand l'utiliser :** régulièrement (par exemple chaque trimestre), pour prouver que la reprise fonctionne et mesurer sa durée face au RTO d'une heure.
**Référence :** premier exercice, 6 min 06 s (Terraform 26 s, Ansible 5 min, restauration 40 s).

## 1. Préparer : des données connues

```
for i in 1 2 3; do curl -s -n -F "file=@/tmp/facture.pdf" https://factures.lab.internal/factures | jq -r .id; done | tee ~/factures-pra.txt
sleep 5
for id in $(cat ~/factures-pra.txt); do curl -s -n https://factures.lab.internal/factures/$id | jq -c '{status, sha256}'; done
cd ~/infra-pme && make backup
ssh -i ~/.ssh/homelab ops@172.31.19.3 "sudo bash -c 'set -a; . /etc/restic/env; restic snapshots --latest 1'"
```

Noter l'identifiant du snapshot et les empreintes. **Ne pas** poser de silence : on mesure aussi la détection.

## 2. Simuler la perte, et chronométrer

```
date +%T | tee ~/pra.log
cd ~/infra-pme/terraform && terraform apply -replace='proxmox_virtual_environment_vm.vm["apps"]'
date +%T | tee -a ~/pra.log
ssh-keygen -R 172.31.19.3
cd ../ansible && ansible-playbook playbooks/site.yml --limit apps
date +%T | tee -a ~/pra.log
ssh -i ~/.ssh/homelab ops@172.31.19.3 "sudo /usr/local/bin/restore-prod.sh [ID du snapshot]"
date +%T | tee -a ~/pra.log
```

## 3. Vérifier

```
for id in $(cat ~/factures-pra.txt); do curl -s -n https://factures.lab.internal/factures/$id | jq -c '{status, sha256}'; done
curl -s -o /dev/null -w "%{http_code}\n" https://vault.lab.internal/alive
```

Mêmes empreintes qu'avant ; Vaultwarden à `200` ; l'alerte reçue sur Discord pendant l'exercice (noter son heure).

## 4. Remettre en état

```
cd ~/infra-pme && make backup && make restore-test
cd terraform && terraform plan && ansible-vault encrypt --output ~/terraform.tfstate.vault terraform.tfstate
```

## 5. Rédiger le post-mortem

Dans `docs/postmortems/[date]-exercice-pra.md` : la chronologie (heures de `~/pra.log` et de l'alerte), la durée face au RTO et face à l'exercice précédent, ce qui a coincé, et les actions correctives (action, responsable, échéance).
