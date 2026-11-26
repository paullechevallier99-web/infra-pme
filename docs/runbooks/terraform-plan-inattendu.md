# Le plan Terraform propose quelque chose d'inattendu

**Quand l'utiliser :** `terraform plan` (ou la confirmation d'un `apply`) veut détruire, remplacer ou créer une VM alors que tu ne l'as pas demandé.
**Impact :** aucun tant que tu n'appliques pas. **Dans le doute, répondre `no`** : un plan refusé ne coûte rien, une VM détruite par erreur coûte une restauration.

## 1. Lire le plan

| Symbole | Signification |
|---|---|
| `+` | Créer |
| `~` | Modifier sur place (la VM reste) |
| `-` | Détruire |
| `-/+` | Détruire puis recréer : **la VM repart vide** |

Chercher la mention `# forces replacement` : elle désigne le réglage qui oblige à recréer la VM.

## 2. Trouver la cause

| Le plan... | Cause probable | Résolution |
|---|---|---|
| Veut **créer** des VM qui existent | État Terraform perdu ou vide | [etat-terraform-perdu.md](etat-terraform-perdu.md) |
| Veut **remplacer** une VM sans raison | État périmé (snapshot de la VM admin restauré), ou réglage modifié dans `ecole.auto.tfvars` | Comparer : `git diff`, et reprendre la copie récente de l'état |
| Veut **modifier** un réglage (mémoire, disque) | Modification faite dans l'interface Proxmox, hors de Terraform | Reporter la valeur dans le code, ou laisser Terraform la remettre |
| Veut remplacer **après une mise à jour du fournisseur** | Nouvelle version de bpg/proxmox qui interprète un réglage autrement | Ne pas appliquer ; lire les notes de version ; revenir à la version précédente dans `providers.tf` et `.terraform.lock.hcl` |
| Touche **backup** | Danger : elle contient les sauvegardes | Ne jamais appliquer sans comprendre ; sa protection Proxmox bloque de toute façon la destruction |

## 3. Cibler une seule ressource

Pour n'agir que sur la VM voulue :

```
terraform apply -replace='proxmox_virtual_environment_vm.vm["apps"]'   # recréer volontairement une VM
terraform plan -target='proxmox_virtual_environment_vm.vm["obs"]'      # voir le plan d'une seule VM
```

## Vérifier

`terraform plan` affiche **No changes**. Après tout `apply` : copie chiffrée de l'état (`ansible-vault encrypt --output ~/terraform.tfstate.vault terraform.tfstate`).
