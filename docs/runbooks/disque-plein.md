# Alerte DiskAlmostFull

**Quand l'utiliser :** moins de 15 % d'espace libre sur un disque, depuis 10 minutes.
**Gravité :** avertissement, qui devient critique si le disque se remplit : les services cessent
d'écrire (base, journaux, sauvegardes).

## 1. Identifier ce qui occupe la place

Ne rien supprimer avant de savoir. Sur la VM concernée :

    df -h
    sudo du -xh / --max-depth=2 2>/dev/null | sort -h | tail -15
    sudo docker system df

## 2. Résoudre selon la cause

| Cause | Résolution |
|---|---|
| Anciennes images Docker | `sudo docker image prune -a` (les images utilisées sont conservées) |
| Journaux système volumineux | `sudo journalctl --vacuum-size=200M` |
| Données Prometheus ou Loki (obs) | Normal jusqu'à la rétention (15 j et 7 j) ; sinon agrandir le disque |
| Dépôt restic (backup) | Vérifier que `restic forget --prune` tourne bien dans la sauvegarde |
| Factures (apps) | Croissance normale : agrandir le disque |

**Ne jamais** lancer `docker system prune --volumes` : les volumes contiennent les données
(PostgreSQL, Redis, Grafana, Prometheus, Loki).

## 3. Agrandir le disque, si nécessaire

Dans `terraform/ecole.auto.tfvars`, augmenter `disk` pour la VM, puis :

    cd ~/infra-pme/terraform && terraform plan      # doit annoncer une modification, pas un remplacement
    terraform apply

Puis, sur la VM : `sudo growpart /dev/sda 1 && sudo resize2fs /dev/sda1`, et `df -h` pour vérifier.
Sauvegarder ensuite l'état Terraform chiffré.

## 4. Vérifier

`df -h` : plus de 15 % libres, puis `[RESOLVED]` sur Discord.
