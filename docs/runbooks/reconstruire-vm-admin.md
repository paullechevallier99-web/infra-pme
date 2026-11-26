# Reconstruire la VM admin (le bastion)

**Quand l'utiliser :** la VM admin est perdue, détruite, ou dans un état inconnu.
**Impact :** les services du cabinet continuent de fonctionner. Seule l'administration est interrompue : plus de déploiement, plus de Terraform, plus d'accès au rebond.

C'est la **seule VM créée à la main** : elle ne se reconstruit pas par le code. D'où l'importance des copies hors de la VM.

## Prérequis : ce qu'il faut avoir hors de la VM admin

| Élément | Où le retrouver |
|---|---|
| Le dépôt | GitHub |
| Le mot de passe du coffre Ansible Vault | Bitwarden |
| La phrase de passe de la clé `homelab` (ou la clé elle-même) | Bitwarden |
| Le jeton Proxmox | Bitwarden, ou en recréer un (Proxmox, **Datacenter**, **Permissions**, **Jetons d'API**) |
| `ecole.auto.tfvars` (valeurs de la plateforme) | Copie chiffrée, ou le recopier depuis le modèle `.example` et la fiche d'environnement |
| L'état Terraform | `terraform.tfstate.vault`, copie chiffrée faite après chaque `apply` |

**Si un snapshot `avant-jury` (ou autre) existe :** le restaurer dans Proxmox est plus rapide. Après restauration : `git pull`, puis reprendre l'état Terraform le plus récent (voir [etat-terraform-perdu.md](etat-terraform-perdu.md)), puis `terraform plan`.

## 1. Recréer la VM

Dans Proxmox : cloner le modèle Debian 13 (n° 120) en **clone intégral**, nom `admin`, 2 processeurs, 2 Go, disque de 20 Go. Onglet **Cloud-Init** : utilisateur `ops`, adresse `172.31.19.1/24`, passerelle `172.31.19.254`, DNS `9.9.9.9`, ta clé publique de poste. **Regénérer l'image**, démarrer.

## 2. Installer les outils

```
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl jq make python3-venv tmux openssl sqlite3
```

Puis Docker (dépôt officiel), Terraform (dépôt HashiCorp), Tailscale, comme dans le guide d'exploitation. Ansible et les outils de vérification dans un environnement Python, aux versions du dépôt :

```
python3 -m venv ~/.venvs/ansible && source ~/.venvs/ansible/bin/activate
git clone git@github.com:paullechevallier99-web/infra-pme.git ~/infra-pme
pip install -r ~/infra-pme/requirements-dev.txt
cd ~/infra-pme/ansible && ansible-galaxy collection install -r requirements.yml
```

(Pour le clone, recréer d'abord la clé de déploiement GitHub, ou cloner en HTTPS.)

## 3. Remettre les secrets

```
mkdir -p ~/.ansible && nano ~/.ansible/vault_pass_homelab && chmod 600 ~/.ansible/vault_pass_homelab
echo 'export ANSIBLE_VAULT_PASSWORD_FILE=~/.ansible/vault_pass_homelab' >> ~/.bashrc
nano ~/.proxmox_token && chmod 600 ~/.proxmox_token
echo 'export PROXMOX_VE_API_TOKEN="$(cat ~/.proxmox_token)"' >> ~/.bashrc
```

La clé `homelab` : la restaurer depuis sa copie. Si elle est perdue, en créer une nouvelle (`ssh-keygen -t ed25519 -f ~/.ssh/homelab`) : il faudra alors la déposer pour `ops` sur les 4 VM, par la console Proxmox, ou recréer les VM.

L'état Terraform : `ansible-vault decrypt --output ~/infra-pme/terraform/terraform.tfstate ~/terraform.tfstate.vault` (après avoir copié le fichier sur la VM).

## 4. Durcir et rouvrir les accès

- SSH : `/etc/ssh/sshd_config.d/10-hardening.conf` (mots de passe et root refusés), `sudo sshd -t && sudo systemctl restart ssh`.
- UFW : SSH depuis les réseaux de l'école et `tailscale0`, puis `sudo ufw enable`.
- Tailscale : `sudo tailscale up`, puis étiquette `tag:bastion` dans la console, et l'annonce du VLAN si tu l'utilises (`sudo tailscale set --advertise-routes=172.31.19.0/24`).

## Vérifier

```
cd ~/infra-pme/terraform && terraform plan                    # No changes
cd ../ansible && ansible all -m ansible.builtin.ping           # pong x4
ansible-playbook playbooks/site.yml --check --diff | tail -5  # changed=0
```

## Après

L'adresse Tailscale de la VM admin a pu changer : mettre à jour le fichier `config` SSH des postes, les règles et le partage du jury. Noter le temps passé : c'est l'argument pour gérer un jour la VM admin elle-même par Ansible.
