# Ouvrir, tester, dépanner et révoquer l'accès du jury

**Quand l'utiliser :** avant l'envoi du dossier (ouvrir et tester), quand le jury signale un problème (dépanner), après l'épreuve (révoquer).
**Périmètre de l'accès :** partage Tailscale de la seule VM admin (port 22), compte `jury` avec `sudo` sur le bastion et sur les 4 VM, rebond par ProxyJump.

## 1. Ouvrir l'accès

1. **Protéger d'abord** : `make backup`, copie chiffrée de l'état Terraform, snapshot Proxmox `avant-jury` de chaque VM, **VM admin comprise** (la seule non reconstructible).
2. **Les 4 VM** : `jury_enabled: true` dans les variables, clé publique dans `ansible/files/jury.pub`, puis `make deploy`.
3. **La VM admin** (à la main) : compte `jury` sans mot de passe, clé dans `/home/jury/.ssh/authorized_keys`, fichier `/etc/ssh/sshd_config.d/20-jury.conf`, et `sudo` :

   ```
   echo "jury ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/jury-admin
   sudo chmod 440 /etc/sudoers.d/jury-admin && sudo visudo -cf /etc/sudoers.d/jury-admin
   sudo sshd -t && sudo systemctl restart ssh
   ```

4. **Tailscale** : la VM admin étiquetée `tag:bastion` ; règle `{"src": ["autogroup:shared"], "dst": ["tag:bastion"], "ip": ["tcp:22"]}` ; partage de la VM admin (**Machines**, `admin`, **⋯**, **Share**).

## 2. Tester (depuis ton PC, avec la clé du jury)

```
ssh jury-admin "whoami && sudo whoami"
ssh jury-apps "whoami && sudo whoami"
ssh jury-edge "whoami && sudo whoami"
ssh jury-obs "whoami && sudo whoami"
ssh jury-backup "whoami && sudo whoami"
ssh -W 172.31.114.1:8006 jury-admin
```

Attendu : `jury` puis `root` partout ; la dernière commande refusée (`administratively prohibited`).

## 3. Dépanner

| Le jury signale | Cause | Résolution |
|---|---|---|
| `Connection timed out` vers `100.88.14.33` | Partage non accepté, ou règle sans `autogroup:shared` | Il doit accepter le partage : `tailscale status` doit lister `admin`. Console : **Access controls**, **Preview rules** |
| Il n'apparaît pas dans **Users** | Normal avec un partage (ce n'est pas une invitation) | Rien à faire |
| `Permission denied (publickey)` | Clé non indiquée, ou phrase de passe erronée | `ssh -i [chemin]/jury_e6 jury@100.88.14.33` ; `IdentitiesOnly yes` dans le fichier `config` |
| Rebond vers une VM refusé | Compte absent de la VM | `jury_enabled: true` puis `make deploy` |
| Sites web inaccessibles | Pas de proxy, ou CA non installée | Proxy SOCKS (`ssh -D 1080 -N jury-admin`) et `ca.crt` (lien GitHub sur la fiche E6) |
| Ne peut pas lancer `make deploy` | Il lui faut la phrase de passe de la clé `homelab` | La lui transmettre si c'est voulu ; sinon, normal |

## 4. Suivre ce qu'il fait

- Sur les 4 VM : Grafana, Explore, Loki : `{source="journal"} |= "sudo" |= "jury"`.
- Sur le bastion (non supervisé) : `sudo journalctl _COMM=sudo --since "7 days ago" | grep jury` et `git status` dans le dépôt.
- Dans Proxmox : ses actions Terraform apparaissent sous ton jeton ; croiser avec le journal `sudo` du bastion.

## 5. Révoquer après l'épreuve

Dans cet ordre :

1. **Couper** : arrêter le partage Tailscale (**Machines**, `admin`, **Share**).
2. **Bastion** : `sudo rm /etc/sudoers.d/jury-admin /etc/ssh/sshd_config.d/20-jury.conf`, `sudo pkill -u jury`, `sudo deluser --remove-home jury`, `sudo sshd -t && sudo systemctl restart ssh`.
3. **Les 4 VM** : `jury_enabled: false`, puis `make deploy`.
4. **Comptes des services** : supprimer les comptes jury de la bibliothèque, de Grafana et de Vaultwarden.
5. **Secrets** (tout a été lisible depuis le bastion) : suivre [secret-compromis.md](secret-compromis.md) en entier : secrets du coffre et `ansible-vault rekey`, jeton Proxmox, clé `homelab`, **PKI** (la clé de la CA est chiffrée avec le mot de passe du coffre).
6. **Vérifier** : `git status`, `ansible-playbook playbooks/site.yml --check --diff`, `terraform plan`, `make restore-test`.
7. Supprimer les snapshots `avant-jury` une fois tout vérifié.
