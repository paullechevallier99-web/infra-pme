# L'état Terraform est perdu, corrompu ou périmé

**Quand l'utiliser :** `terraform.tfstate` a disparu, `terraform plan` veut créer des VM qui existent déjà, ou veut détruire des VM sans raison après la restauration d'un snapshot de la VM admin.
**Impact :** aucun sur les services. Mais **ne rien appliquer** : un `apply` avec un mauvais état peut détruire ou dupliquer des VM.

## 1. Constater

```
cd ~/infra-pme/terraform && ls -l terraform.tfstate*
terraform state list
terraform plan
```

| Constat | Cause | Aller à |
|---|---|---|
| Pas de fichier, `state list` vide, le plan veut **créer** 4 VM | État perdu | 2 |
| Le plan veut **remplacer** une VM que tu n'as pas touchée | État périmé (ancien snapshot de la VM admin, ou VM recréée ailleurs) | 2 |
| Erreur de lecture du fichier | État corrompu | 2 (copie) ou `terraform.tfstate.backup` |
| `Error acquiring the state lock` | Une autre commande tourne, ou s'est mal terminée | 4 |

## 2. Reprendre la copie chiffrée la plus récente

```
cp terraform.tfstate terraform.tfstate.casse 2>/dev/null
ansible-vault decrypt --output terraform.tfstate ~/terraform.tfstate.vault
terraform plan
```

Si le plan affiche **No changes** : terminé. Terraform garde aussi `terraform.tfstate.backup`, l'état précédent : utile si la dernière commande a abîmé le fichier.

## 3. Aucune copie : réimporter les VM existantes

Terraform peut **réapprendre** qu'une VM existante lui appartient. Pour chaque VM (identifiants : edge 996, apps 997, obs 998, backup 999) :

```
terraform import 'proxmox_virtual_environment_vm.vm["apps"]' pve-3/997
```

(Le format exact de l'identifiant à importer dépend du fournisseur bpg/proxmox : vérifier sa documentation avant.) Puis `terraform plan` : quelques différences de réglages sont possibles ; aucune ne doit être un **remplacement**. Si c'est le cas, ne rien appliquer et comparer le code aux réglages réels.

## 4. Verrou bloqué

S'assurer qu'aucune commande Terraform ne tourne (autre session tmux), puis :

```
terraform force-unlock [identifiant affiché dans l'erreur]
```

## Vérifier

`terraform plan` : **No changes. Your infrastructure matches the configuration.**

## Après

Refaire tout de suite la copie chiffrée :

```
ansible-vault encrypt --output ~/terraform.tfstate.vault terraform.tfstate
```

et la ranger hors de la VM admin. L'amélioration qui supprime ce risque : un état distant (sur Garage ou un stockage S3 externe), avec verrouillage.
