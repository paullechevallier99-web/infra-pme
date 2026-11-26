# Alertes BackupTooOld et BackupMetricMissing

**Quand l'utiliser :**
- `BackupTooOld` : aucune sauvegarde **réussie** depuis plus de 26 h (24 h + marge pour l'heure
  de passage). Elle n'a pas tourné, ou elle a tourné et échoué.
- `BackupMetricMissing` : la métrique de sauvegarde n'existe pas depuis 1 h (script jamais lancé,
  ou collecte cassée).

**Gravité :** critique.
**Impact :** le RPO de 24 h n'est plus garanti. Si apps tombait maintenant, plus d'une journée de
données serait perdue.

La sauvegarde est exécutée par la VM **apps**, et envoyée vers Garage sur **backup**.

## 1. Diagnostiquer, sur apps

    ssh -i ~/.ssh/homelab ops@172.31.19.3
    sudo journalctl -u restic-backup.service -n 50 --no-pager      # l'erreur exacte
    systemctl list-timers | grep restic                             # la minuterie a-t-elle tourné ?
    cat /var/lib/node_exporter/textfile/backup.prom                 # la métrique existe-t-elle ?
    curl -s -o /dev/null -w "%{http_code}\n" http://172.31.19.5:3900   # Garage répond-il ?

| Constat | Cause | Résolution |
|---|---|---|
| Pas de passage cette nuit | Minuterie arrêtée, VM éteinte la nuit | `sudo systemctl enable --now restic-backup.timer` |
| Garage injoignable (000) | VM backup arrêtée, Garage arrêté, pare-feu | Voir 2a |
| Erreur d'authentification S3 | Clés Garage changées | Vérifier `vault_restic_s3_key_id` et `vault_restic_s3_secret`, redéployer apps |
| `pg_dump` en échec | PostgreSQL arrêté | `sudo docker compose -f /opt/apps/compose.yml ps` |
| Disque plein | Sur apps ou sur backup | [disque-plein.md](disque-plein.md) |
| Fichier `.prom` absent | Script jamais lancé, ou dossier absent | Redéployer apps, puis relancer la sauvegarde |

**2a. Garage.** Sur backup :

    sudo docker ps --format "{{.Names}}  {{.Status}}" | grep garage
    sudo docker exec garage /garage status
    df -h /srv/garage

## 2. Relancer la sauvegarde

Depuis la VM admin :

    cd ~/infra-pme && make backup

## 3. Vérifier

    ssh -i ~/.ssh/homelab ops@172.31.19.3 'sudo journalctl -u restic-backup.service -n 10 --no-pager'
    ssh -i ~/.ssh/homelab ops@172.31.19.3 "sudo bash -c 'set -a; . /etc/restic/env; restic snapshots --latest 1'"

Un snapshot daté de maintenant, et `[RESOLVED]` sur Discord.

## 4. Après

Lancer aussi un test de restauration (`make restore-test`) : une sauvegarde réussie n'est une
garantie que si elle se restaure.
