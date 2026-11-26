# Reconstruire une VM perdue (edge, apps ou obs)

**Quand l'utiliser :** une VM est détruite, irrécupérable, ou dans un état inconnu (après une
modification non maîtrisée).
**Impact :** les services de la VM sont indisponibles pendant la reconstruction (mesuré : 6 min 06 s
pour apps, restauration comprise).

| VM | Adresse | Données à restaurer après |
|---|---|---|
| edge | 172.31.19.2 | Aucune |
| apps | 172.31.19.3 | Oui : [restauration.md](restauration.md) |
| obs | 172.31.19.4 | Aucune (l'historique des métriques et journaux est perdu ; les tableaux de bord reviennent) |

La VM **backup** ne se reconstruit pas ainsi : elle est protégée, et contient les sauvegardes.

## Prérequis

    eval "$(ssh-agent -s)" && ssh-add ~/.ssh/homelab
    export PROXMOX_VE_API_TOKEN="$(cat ~/.proxmox_token)"

Pour apps : **noter avant tout** l'identifiant du dernier snapshot antérieur à l'incident
(voir [restauration.md](restauration.md)).

## 1. Recréer la VM

    date +%T | tee ~/reconstruction.log
    cd ~/infra-pme/terraform
    terraform apply -replace='proxmox_virtual_environment_vm.vm["[vm]"]'

Avant de confirmer, lire le plan : **1 to add, 0 to change, 1 to destroy**, uniquement la VM visée.
Tout autre plan : répondre `no`.

## 2. La reconfigurer

    ssh-keygen -R 172.31.19.[X]
    cd ~/infra-pme/ansible && ansible-playbook playbooks/site.yml --limit [vm]

Attendu : `failed=0`.

## 3. Restaurer les données (apps uniquement)

[restauration.md](restauration.md), avec l'identifiant de snapshot noté au départ.

## 4. Vérifier

    date +%T | tee -a ~/reconstruction.log
    cd ~/infra-pme/ansible && ansible-playbook playbooks/site.yml --limit [vm] --check --diff | tail -3
    curl -s https://factures.lab.internal/healthz; echo

## 5. Après

    cd ~/infra-pme && make backup && make restore-test
    cd terraform && terraform plan       # No changes
    ansible-vault encrypt --output ~/terraform.tfstate.vault terraform.tfstate

L'état Terraform a changé : ranger sa copie chiffrée hors de la VM admin. Rédiger le post-mortem
dans `docs/postmortems/`.
