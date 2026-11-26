# Une VM ne démarre pas, ou démarre mal

**Quand l'utiliser :** la VM est arrêtée et refuse de démarrer, reste bloquée au démarrage, ou démarre sans adresse IP.
**Impact :** tous les services de la VM sont arrêtés.

## 1. Regarder dans Proxmox

Interface Proxmox, la VM, onglet **Résumé** et journal des **Tâches** (en bas de l'écran).

| Constat | Cause probable | Aller à |
|---|---|---|
| La tâche « Start » échoue avec un message | Ressources, stockage, verrou | 2 |
| Elle démarre, mais la console reste sur un écran d'erreur | Disque, système de fichiers, noyau | 3 |
| Elle démarre, la console affiche une invite, mais pas de réseau | cloud-init ou configuration réseau | 4 |
| Elle démarre normalement, mais les services ne reviennent pas | Docker ou un conteneur | 5 |

## 2. Le démarrage échoue dans Proxmox

| Message | Cause | Résolution |
|---|---|---|
| `VM is locked (backup)` ou `(snapshot)` | Une opération est en cours ou a été interrompue | Attendre ; si elle est bloquée, demander à l'enseignant (commande `qm unlock` réservée à l'hyperviseur) |
| Mémoire insuffisante | Le serveur est plein | Attendre, ou réduire la mémoire de la VM dans `ecole.auto.tfvars` puis `terraform apply` |
| Erreur de stockage | Stockage plein ou indisponible | Prévenir l'enseignant : hors de ton périmètre |
| `quota` ou `pool` | Quota du pool atteint | Supprimer des snapshots inutiles, ou demander un quota |

## 3. Bloquée au démarrage

Ouvrir la **console** de la VM :

| Constat | Résolution |
|---|---|
| Message de système de fichiers (`fsck`, « emergency mode ») | Disque abîmé ou plein : la VM est reconstructible, la reconstruire ([reconstruire-une-vm.md](reconstruire-une-vm.md)) plutôt que réparer à la main |
| Disque plein au démarrage | Voir [disque-plein.md](disque-plein.md) ; si inaccessible, reconstruire |
| Panique du noyau après une mise à jour | Redémarrer et choisir le noyau précédent dans le menu de démarrage, puis prévenir |

Pour **apps**, une reconstruction implique une restauration des données : noter **avant** l'identifiant du dernier snapshot restic.

## 4. Pas de réseau, ou pas d'utilisateur ops

Le plus souvent : cloud-init n'a pas pu s'appliquer (VM recréée, modèle modifié).

- Console : `cloud-init status --long` puis `ip -br a`.
- Si `ip -br a` ne montre pas l'adresse `172.31.19.[X]`, vérifier dans Proxmox l'onglet **Cloud-Init** de la VM : adresse, passerelle, DNS, utilisateur.
- Le plus sûr : recréer la VM par Terraform, qui réécrit toute la configuration cloud-init.

## 5. La VM tourne, mais pas ses services

```
ssh ops@172.31.19.[X]      # depuis la VM admin
sudo systemctl status docker --no-pager | head -5
sudo docker ps -a --format "{{.Names}}  {{.Status}}"
```

- Docker arrêté : `sudo systemctl start docker`.
- Conteneurs arrêtés : relancer la stack, par exemple `sudo docker compose -f /opt/apps/compose.yml up -d`, et `/opt/agents/compose.yml`.
- Filtrage : `sudo systemctl status docker-user-filter --no-pager` doit être `active`.

## Vérifier

Depuis la VM admin : `ansible all -m ansible.builtin.ping`, puis les tests de services :

```
curl -s https://factures.lab.internal/healthz; echo
curl -s -o /dev/null -w "%{http_code}\n" https://vault.lab.internal/alive
```

## Après

Un redémarrage complet de la plateforme est normalement transparent : les VM démarrent seules (`on_boot`), Docker relance les conteneurs, le filtrage se réapplique. Si ce n'est pas le cas, noter ce qui n'est pas revenu dans un post-mortem.
