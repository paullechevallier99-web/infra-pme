# Runbooks

Un runbook est une procédure écrite et testée pour une situation précise : on la suit le jour
de l'incident, au lieu d'improviser. Chaque runbook suit le même plan : quand l'utiliser,
impact, prérequis, diagnostic, résolution, vérification, après l'incident.

## Par alerte

| Alerte | Gravité | Runbook |
|---|---|---|
| InstanceDown | Critique | [instance-down.md](instance-down.md) |
| ServiceProbeFailed | Critique | [service-probe-failed.md](service-probe-failed.md) |
| BackupTooOld, BackupMetricMissing | Critique | [backup-too-old.md](backup-too-old.md) |
| RestoreTestTooOld | Avertissement | [restore-test-too-old.md](restore-test-too-old.md) |
| DiskAlmostFull | Avertissement | [disque-plein.md](disque-plein.md) |
| MemoryPressure, ContainerRestarting | Avertissement | [memoire-et-conteneurs.md](memoire-et-conteneurs.md) |
| InvoiceQueueBacklog, ClassementDegrade | Avertissement | [classement-factures.md](classement-factures.md) |
| CertificateExpiringSoon | Avertissement | [renouveler-certificat.md](renouveler-certificat.md) |

## Par situation

| Situation | Runbook |
|---|---|
| Restaurer les données de la VM apps | [restauration.md](restauration.md) |
| Reconstruire une VM perdue (edge, apps ou obs) | [reconstruire-une-vm.md](reconstruire-une-vm.md) |
| Initialiser Garage (première installation, ou VM backup perdue) | [initialiser-garage.md](initialiser-garage.md) |

## Avant toute intervention

Sur la VM admin :

    tmux new -s incident || tmux attach -t incident
    eval "$(ssh-agent -s)" && ssh-add ~/.ssh/homelab
    cd ~/infra-pme && git pull

Pendant une intervention prévue, poser un silence pour ne pas déclencher d'alertes inutiles :

    ssh -i ~/.ssh/homelab ops@172.31.19.4 \
      "sudo docker exec obs-alertmanager-1 amtool silence add host=[vm] --duration=30m \
       --comment='Intervention prévue' --alertmanager.url=http://localhost:9093"

Après chaque incident : noter ce qui s'est passé dans `docs/postmortems/`, et reporter dans le
code toute correction faite à la main, pour qu'elle survive à la prochaine reconstruction.
