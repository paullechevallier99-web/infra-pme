# Une VM est injoignable en SSH

**Quand l'utiliser :** `ssh` vers une VM (ou vers la VM admin) échoue, ou Ansible affiche `UNREACHABLE`.
**Impact :** plus d'administration de cette VM. Ses services peuvent fonctionner normalement.

## 1. Lire le message exact

Le message de `ssh` dit presque toujours où est le problème :

```
ssh -v -i ~/.ssh/homelab ops@172.31.19.[X] 2>&1 | tail -15
```

| Message | Signification | Aller à |
|---|---|---|
| `Connection timed out` | Aucune réponse : VM éteinte, réseau coupé, ou pare-feu qui ignore | 2 |
| `Connection refused` | La VM répond, mais rien n'écoute sur le port 22 : SSH arrêté | 3 |
| `Permission denied (publickey)` | SSH répond, mais refuse la clé | 4 |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | La VM a été recréée : nouvelle clé d'hôte | 5 |
| `Too many authentication failures` | Trop de clés proposées avant la bonne | 6 |

## 2. Délai dépassé (timed out)

```
ping -c 3 172.31.19.[X]
```

- **Pas de réponse au ping** : dans l'interface Proxmox, vérifier que la VM est démarrée (`running`). Éteinte : la démarrer. Démarrée mais muette : ouvrir sa **console** (bouton Console, noVNC) et voir [vm-ne-demarre-pas.md](vm-ne-demarre-pas.md).
- **Ping OK mais SSH muet** : le pare-feu de la VM ignore ta source. Les VM n'acceptent SSH **que depuis la VM admin** (172.31.19.1) : depuis ton PC, il faut passer par le bastion (`ssh -J ops@100.88.14.33 ops@172.31.19.[X]`).
- **Depuis la VM admin elle-même** : par la console Proxmox de la VM visée, `sudo ufw status` doit montrer `22/tcp ALLOW 172.31.19.1`.

## 3. Connexion refusée (refused)

SSH est arrêté, souvent après une erreur dans sa configuration. Par la **console Proxmox** de la VM (connexion `ops`, pas de mot de passe : si la console demande un mot de passe, voir la remarque en fin de fiche) :

```
sudo sshd -t                                   # affiche l'erreur de configuration, ou rien si tout va bien
sudo systemctl status ssh --no-pager | head -8
```

Corriger le fichier cité (souvent `/etc/ssh/sshd_config.d/10-hardening.conf` ou `20-jury.conf`), puis :

```
sudo sshd -t && sudo systemctl restart ssh
```

Ensuite, depuis la VM admin, redéployer la VM pour remettre la configuration exacte du dépôt :
`cd ~/infra-pme/ansible && ansible-playbook playbooks/site.yml --limit [vm]`.

## 4. Clé refusée (Permission denied)

| Constat | Cause | Résolution |
|---|---|---|
| `ssh-add -l` : « The agent has no identities » | Clé non chargée | `eval "$(ssh-agent -s)" && ssh-add ~/.ssh/homelab` |
| Mauvais utilisateur (`root`, `debian`) | Seul `ops` est autorisé (`AllowUsers`) | `ssh ops@...` |
| Clé absente de la VM (VM recréée à la main) | `authorized_keys` vide | Console Proxmox : vérifier `~ops/.ssh/authorized_keys` ; sinon recréer la VM par Terraform |
| Compte jury | Clé `jury_e6` non indiquée | `ssh -i ~/.ssh/jury_e6 ...` ou les blocs `jury-*` du fichier `config` |

## 5. Identité changée

Normal après `terraform apply -replace` : la VM neuve a une nouvelle clé d'hôte.

```
ssh-keygen -R 172.31.19.[X]
```

**Attention :** si la VM n'a **pas** été recréée, ce message peut signaler une usurpation. Vérifier dans Proxmox (date de création de la VM, journal des tâches) avant de supprimer l'ancienne empreinte.

## 6. Trop d'échecs d'authentification

L'agent propose toutes ses clés, et la VM coupe après 3 essais (`MaxAuthTries 3`). Forcer la bonne clé :

```
ssh -o IdentitiesOnly=yes -i ~/.ssh/homelab ops@172.31.19.[X]
```

## Vérifier

```
cd ~/infra-pme/ansible && ansible all -m ansible.builtin.ping
```

`pong` pour les quatre VM.

## Remarque : la console Proxmox demande un mot de passe

Le compte `ops` n'a pas de mot de passe (connexion par clé uniquement). Si la console est indispensable, deux possibilités : redémarrer la VM et utiliser la console pour lire les messages de démarrage, ou, si la VM est irrécupérable, la reconstruire ([reconstruire-une-vm.md](reconstruire-une-vm.md)). C'est le prix d'une configuration sans mot de passe, et la raison pour laquelle tout est reconstructible.
