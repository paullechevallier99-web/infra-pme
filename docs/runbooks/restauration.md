# Restaurer les données de la VM apps

Impact : Vaultwarden et l'application factures sont indisponibles pendant la restauration.

## Prérequis

1. Sur la VM admin, la clé `homelab` est chargée : `ssh-add -l` doit la lister.
   Sinon : `eval "$(ssh-agent -s)" && ssh-add ~/.ssh/homelab`.
2. Le jeton Proxmox est chargé, si la VM doit être recréée : `[ -n "$PROXMOX_VE_API_TOKEN" ]`.

## Choisir le snapshot

    ssh -i ~/.ssh/homelab ops@172.31.19.3 "sudo bash -c 'set -a; . /etc/restic/env; restic snapshots'"

Choisir le snapshot dont l'heure précède **immédiatement** l'incident.
Ne jamais utiliser `latest` après une reconstruction : la sauvegarde la plus récente
peut être celle d'une VM vide.

## Restaurer

    ssh -i ~/.ssh/homelab ops@172.31.19.3 "sudo /usr/local/bin/restore-prod.sh [ID]"

La dernière ligne indique le nombre de factures restaurées : le comparer au nombre attendu.

## Vérifier

    curl -s https://factures.lab.internal/factures/[ID d'une facture connue] | jq
    curl -s -o /dev/null -w "%{http_code}\n" https://vault.lab.internal/alive
