# Runbooks

Un runbook est une procédure écrite et testée pour une situation précise : on la suit le jour de l'incident, au lieu d'improviser. Chacun suit le même plan : quand l'utiliser, impact, diagnostic (constat, cause, résolution), vérification, et ce qu'il faut faire après.

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

### Accès

| Situation | Runbook |
|---|---|
| Une VM est injoignable en SSH (délai, refus, clé refusée, identité changée) | [acces-ssh-impossible.md](acces-ssh-impossible.md) |
| Une VM ne démarre pas, ou démarre sans réseau | [vm-ne-demarre-pas.md](vm-ne-demarre-pas.md) |
| Plus d'accès à distance par Tailscale | [acces-distant-tailscale.md](acces-distant-tailscale.md) |
| Les sites ne s'ouvrent pas dans le navigateur | [acces-sites-web.md](acces-sites-web.md) |
| Ouvrir, tester, dépanner et révoquer l'accès du jury | [acces-jury.md](acces-jury.md) |

### Reconstruire et restaurer

| Situation | Runbook |
|---|---|
| Recréer edge, apps ou obs | [reconstruire-une-vm.md](reconstruire-une-vm.md) |
| Recréer la VM admin (le bastion) | [reconstruire-vm-admin.md](reconstruire-vm-admin.md) |
| Recréer la VM backup | [reconstruire-vm-backup.md](reconstruire-vm-backup.md) |
| Perte de toute la plateforme Proxmox | [perte-plateforme-proxmox.md](perte-plateforme-proxmox.md) |
| État Terraform perdu, corrompu ou périmé | [etat-terraform-perdu.md](etat-terraform-perdu.md) |
| Restaurer toutes les données de apps | [restauration.md](restauration.md) |
| Restaurer une facture, la base seule, ou Vaultwarden seul | [restauration-partielle.md](restauration-partielle.md) |
| Préparer Garage (installation, ou VM backup recréée) | [initialiser-garage.md](initialiser-garage.md) |

### Services

| Situation | Runbook |
|---|---|
| PostgreSQL ou Redis en panne | [postgresql-redis.md](postgresql-redis.md) |
| Vaultwarden : panne, création de compte, jeton d'administration, mot de passe maître perdu | [vaultwarden.md](vaultwarden.md) |
| Créer, changer ou supprimer un accès (bibliothèque, Grafana, Vaultwarden) | [gerer-les-comptes.md](gerer-les-comptes.md) |

### Supervision et réseau

| Situation | Runbook |
|---|---|
| obs, Prometheus, Grafana ou Loki hors service | [supervision-hors-service.md](supervision-hors-service.md) |
| Les alertes n'arrivent pas sur Discord | [alertes-non-recues.md](alertes-non-recues.md) |
| Grafana affiche « No data » | [grafana-no-data.md](grafana-no-data.md) |
| Un flux légitime est bloqué par le pare-feu | [flux-bloque-pare-feu.md](flux-bloque-pare-feu.md) |

### Déployer et mettre à jour

| Situation | Runbook |
|---|---|
| Un déploiement Ansible échoue | [deploiement-ansible-echoue.md](deploiement-ansible-echoue.md) |
| Le plan Terraform propose quelque chose d'inattendu | [terraform-plan-inattendu.md](terraform-plan-inattendu.md) |
| L'intégration continue est rouge | [ci-bloquee.md](ci-bloquee.md) |
| Appliquer une mise à jour, et revenir en arrière | [mettre-a-jour-et-revenir-en-arriere.md](mettre-a-jour-et-revenir-en-arriere.md) |

### Sécurité

| Situation | Runbook |
|---|---|
| Un secret est compromis (coffre, jeton, clé, CA, fuite sur GitHub) | [secret-compromis.md](secret-compromis.md) |
| Une intrusion est suspectée | [intrusion-suspectee.md](intrusion-suspectee.md) |

### Exploitation courante

| Situation | Runbook |
|---|---|
| Vérifications de chaque séance et de chaque semaine | [verifications-regulieres.md](verifications-regulieres.md) |
| Préparer et mener une maintenance | [maintenance-planifiee.md](maintenance-planifiee.md) |
| Mener un exercice de reprise chronométré | [exercice-pra.md](exercice-pra.md) |

## Avant toute intervention

Sur la VM admin :

```
tmux new -s incident || tmux attach -t incident
eval "$(ssh-agent -s)" && ssh-add ~/.ssh/homelab
cd ~/infra-pme && git pull
```

Après chaque incident : le noter dans `docs/postmortems/`, et reporter dans le code toute correction faite à la main, pour qu'elle survive à la prochaine reconstruction.
