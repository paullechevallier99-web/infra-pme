# Reconstruire la VM backup

**Quand l'utiliser :** la VM backup est perdue, ou son disque est inutilisable.
**Impact :** les services continuent, mais **les sauvegardes stockées sont perdues** (aucune copie hors site aujourd'hui). La sauvegarde de la nuit échouera tant que la VM n'est pas reconstruite.

**À ne jamais faire par réflexe :** la VM backup est protégée, et exclue de `make rebuild`, justement parce qu'elle contient les sauvegardes. Ne la reconstruire que si elle est **réellement** perdue.

## 1. Constater la perte

```
ping -c 3 172.31.19.5
ssh -i ~/.ssh/homelab ops@172.31.19.5 'sudo docker ps; df -h /srv/garage'
```

Si la VM répond, chercher d'abord à réparer ([instance-down.md](instance-down.md), [disque-plein.md](disque-plein.md)) : une reconstruction efface tout.

## 2. Lever la protection, puis recréer

Dans Proxmox : VM 999, **Options**, **Protection** : décocher. Puis, depuis la VM admin :

```
cd ~/infra-pme/terraform
terraform apply -replace='proxmox_virtual_environment_vm.vm["backup"]'
```

Lire le plan : **1 to add, 0 to change, 1 to destroy**, uniquement `vm["backup"]`. Terraform la recrée **avec** la protection (elle est dans le code).

## 3. La reconfigurer

```
ssh-keygen -R 172.31.19.5
cd ~/infra-pme/ansible && ansible-playbook playbooks/site.yml --limit backup
```

## 4. Réinitialiser Garage

Garage est vide : refaire l'initialisation manuelle ([initialiser-garage.md](initialiser-garage.md)) : organisation du stockage, compartiment `restic`, clé `restic-key`, autorisations. **La clé générée est nouvelle** : reporter son identifiant et son secret dans le coffre (`vault_restic_s3_key_id`, `vault_restic_s3_secret`).

## 5. Recréer le dépôt restic et sauvegarder tout de suite

```
cd ~/infra-pme/ansible && ansible-playbook playbooks/site.yml --limit apps   # dépose les nouvelles clés, initialise le dépôt restic vide
cd ~/infra-pme && make backup && make restore-test
```

## Vérifier

```
ssh -i ~/.ssh/homelab ops@172.31.19.3 "sudo bash -c 'set -a; . /etc/restic/env; restic snapshots'"
```

Un snapshot de maintenant. L'alerte `BackupTooOld` passe à `RESOLVED`.

## Après

L'historique des sauvegardes est perdu : jusqu'à demain, une seule sauvegarde existe. C'est exactement le risque que corrigerait une copie hors site (`restic copy` vers un stockage externe) : à noter dans le post-mortem.
