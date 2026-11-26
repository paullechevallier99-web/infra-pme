# Un secret est compromis

**Quand l'utiliser :** un secret a pu être lu par quelqu'un qui ne devait pas : commité en clair, affiché à l'écran, envoyé par erreur, ou accessible pendant un accès temporaire (le jury, par exemple).
**Principe :** un secret exposé est compromis, même s'il a été supprimé ensuite. On ne le cache pas : on le **remplace**.

## 1. Identifier ce qui est exposé

| Exposé | Ce qu'il ouvre | Aller à |
|---|---|---|
| Un secret du coffre (base, Grafana, restic, Garage, Discord…) | Le service concerné | 2 |
| Le **mot de passe du coffre** | **Tous** les secrets, et la clé de la CA | 2, 3, 4 |
| Le jeton Proxmox | Créer et détruire les VM du pool | 5 |
| La clé `homelab` (et sa phrase de passe) | `root` sur les 4 VM | 6 |
| La clé privée de la CA | Signer un certificat pour n'importe quel site | 4 |
| Un secret poussé sur GitHub | Tout le monde l'a vu | 7, puis selon le secret |

## 2. Régénérer les secrets du coffre

```
cd ~/infra-pme/ansible
ansible-vault edit inventories/lab/group_vars/all/vault.yml
```

Pour chaque secret exposé, une nouvelle valeur (`openssl rand -base64 24`). Cas particuliers :

| Secret | Attention |
|---|---|
| `vault_postgres_password` | PostgreSQL ne le lit qu'à la création : le changer aussi dans la base (`ALTER USER factures PASSWORD '...'`) avant de déployer |
| `vault_restic_password` | Ne pas le remplacer dans le coffre seul : ajouter une nouvelle clé au dépôt (`restic key add`), puis retirer l'ancienne (`restic key remove`), sinon les sauvegardes deviennent illisibles |
| Clés Garage | Créer une nouvelle clé dans Garage, l'autoriser sur le compartiment, supprimer l'ancienne |
| `vault_discord_webhook` | Supprimer l'ancien webhook dans Discord, en créer un nouveau |
| `vault_grafana_admin_password` | Le changer aussi dans Grafana ([gerer-les-comptes.md](gerer-les-comptes.md)) |

Puis `make deploy`.

## 3. Changer le mot de passe du coffre

```
cd ~/infra-pme
ansible-vault rekey ansible/inventories/lab/group_vars/all/vault.yml pki/ca.key pki/wildcard.key
```

Mettre le nouveau mot de passe dans `~/.ansible/vault_pass_homelab` et dans Bitwarden. Rechiffrer aussi la copie de l'état Terraform.

## 4. Régénérer la PKI

Si la clé de la CA a pu être lue (directement, ou par le mot de passe du coffre) : nouvelle CA, nouveau certificat, clés chiffrées, déploiement de edge, puis **réinstaller la nouvelle CA sur chaque poste** et retirer l'ancienne. Procédure de création : [renouveler-certificat.md](renouveler-certificat.md), en recréant aussi `ca.key` et `ca.crt`.

## 5. Révoquer le jeton Proxmox

Proxmox, **Datacenter**, **Permissions**, **Jetons d'API** : supprimer le jeton, en créer un nouveau, le mettre dans `~/.proxmox_token` et dans Bitwarden.

## 6. Remplacer la clé homelab

```
ssh-keygen -t ed25519 -f ~/.ssh/homelab-neuve
```

Déposer la nouvelle clé publique pour `ops` sur les 4 VM (une tâche `authorized_key` dans Ansible, lancée encore avec l'ancienne clé), vérifier la connexion avec la nouvelle, puis retirer l'ancienne des VM et remplacer `~/.ssh/homelab`. Mettre à jour `ssh_public_key_file` pour Terraform.

## 7. Un secret poussé sur GitHub

Le remplacer **d'abord** (points précédents), puis nettoyer l'historique (`git filter-repo`), forcer la publication, et vérifier avec gitleaks :

```
gitleaks git --redact .
```

Le nettoyage ne rend pas le secret à nouveau sûr : il a pu être copié entre-temps.

## Vérifier

`make deploy` à `changed=0` au second passage, services en ligne, `make restore-test` réussi, gitleaks sans fuite.
