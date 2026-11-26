# Alerte RestoreTestTooOld

**Quand l'utiliser :** aucun test de restauration réussi depuis plus de 8 jours. Le test tourne
chaque dimanche à 4 h sur apps : un dimanche a été manqué, ou le test a échoué.
**Gravité :** avertissement.
**Impact :** on ne sait plus si les sauvegardes sont restaurables.

## 1. Diagnostiquer, sur apps

    ssh -i ~/.ssh/homelab ops@172.31.19.3
    sudo journalctl -u restic-restore-test.service -n 40 --no-pager
    systemctl list-timers | grep restore

| Constat | Cause | Résolution |
|---|---|---|
| Pas de passage dimanche | VM éteinte, minuterie arrêtée | `sudo systemctl enable --now restic-restore-test.timer` |
| `integrity_check` différent de `ok` | Base Vaultwarden de la sauvegarde corrompue | Vérifier la sauvegarde précédente ; voir [backup-too-old.md](backup-too-old.md) |
| `pg_restore` en échec | Sauvegarde PostgreSQL inutilisable | Lancer une sauvegarde neuve, puis retester |
| Erreur restic | Garage injoignable, mot de passe | Voir [backup-too-old.md](backup-too-old.md) |

## 2. Relancer et vérifier

    cd ~/infra-pme && make restore-test
    ssh -i ~/.ssh/homelab ops@172.31.19.3 'sudo journalctl -u restic-restore-test.service -n 3 --no-pager'

`Restauration valide : N factures`, puis `[RESOLVED]` sur Discord.
