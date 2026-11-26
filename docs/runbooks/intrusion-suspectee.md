# Une intrusion est suspectée

**Quand l'utiliser :** une activité anormale : connexions SSH inconnues, commande `sudo` inexpliquée, fichier modifié sans raison, service qui consomme sans raison, compte inconnu.
**Principe :** constater et garder les traces, isoler, puis **reconstruire** plutôt que nettoyer : une machine compromise n'est plus digne de confiance, et la tienne se reconstruit par le code.

## 1. Constater, sans effacer les traces

Les journaux des 4 VM sont centralisés sur obs : un attaquant sur une VM ne peut pas effacer ce qui est déjà parti vers Loki. Dans Grafana, Explore, Loki :

```
{source="journal"} |~ "Accepted|Failed|Invalid user"      # connexions SSH
{source="journal"} |= "sudo"                               # commandes d'administration
```

Sur le bastion (non supervisé) :

```
sudo journalctl _COMM=sshd --since "2 days ago" | grep -E "Accepted|Failed"
sudo journalctl _COMM=sudo --since "2 days ago"
last -n 20
cd ~/infra-pme && git status && git log --oneline -5
```

Et la dérive des VM par rapport au dépôt :

```
cd ~/infra-pme/ansible && ansible-playbook playbooks/site.yml --check --diff
```

Noter l'heure, les adresses, les comptes : ce sera le post-mortem.

## 2. Isoler

| Situation | Action |
|---|---|
| Accès par Tailscale suspect | Console Tailscale : retirer l'appareil ou le partage concerné |
| Compte suspect sur une VM | `sudo pkill -u [compte]` ; verrouiller le compte |
| VM suspecte | Dans Proxmox, **déconnecter sa carte réseau** (plutôt que l'éteindre : la mémoire reste examinable), ou prendre un snapshot pour l'analyse |

## 3. Reconstruire

Les 4 VM se reconstruisent depuis le dépôt ([reconstruire-une-vm.md](reconstruire-une-vm.md)) ; pour apps, restaurer une sauvegarde **antérieure** à l'intrusion. Le bastion compromis : [reconstruire-vm-admin.md](reconstruire-vm-admin.md).

## 4. Considérer les secrets comme compromis

Tout ce qui était lisible depuis la machine touchée : [secret-compromis.md](secret-compromis.md). Si c'est le bastion : **tous** les secrets, le jeton Proxmox, la clé `homelab` et la PKI.

## Vérifier

`--check --diff` à `changed=0` sur des VM neuves, nouveaux secrets en place, plus aucune connexion inconnue dans les journaux.

## Après

Post-mortem : par où l'attaquant est entré, et la mesure qui l'aurait empêché. Prévenir le responsable du cabinet (et, dans un cas réel, évaluer les obligations de signalement si des données personnelles sont concernées).
