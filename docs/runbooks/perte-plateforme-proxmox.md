# La plateforme Proxmox est perdue

**Quand l'utiliser :** la plateforme de l'école est indisponible durablement, réinitialisée, ou toutes les VM ont disparu.
**Impact :** tout est arrêté : services, supervision, **et sauvegardes** (elles sont sur la même plateforme).

C'est la limite principale de l'infrastructure : sans copie hors site, **les données sont perdues**. Ce que tu peux reconstruire, c'est la **plateforme**, pas les données.

## 1. Évaluer

| Situation | Conséquence |
|---|---|
| Panne temporaire (coupure, maintenance) | Attendre : au retour, les VM démarrent seules. Vérifier ensuite ([vm-ne-demarre-pas.md](vm-ne-demarre-pas.md)) |
| Plateforme réinitialisée, VM supprimées | Reconstruction complète, sans les données |
| Nouvelle plateforme (autre serveur, autre école) | Reconstruction complète, après adaptation des valeurs |

Prévenir l'enseignant : c'est hors de ton périmètre.

## 2. Reconstruire depuis le dépôt

1. Recréer la VM admin à la main : [reconstruire-vm-admin.md](reconstruire-vm-admin.md).
2. Adapter `ecole.auto.tfvars` : nœud, pool, stockage, pont, modèle, plage d'identifiants, réseau.
3. L'ancien état Terraform décrit des VM qui n'existent plus : repartir d'un état **vide** (le mettre de côté : `mv terraform.tfstate terraform.tfstate.ancien`).
4. Créer les VM et tout configurer :

   ```
   cd ~/infra-pme && make up && make deploy-initial
   ```

5. Initialiser Garage ([initialiser-garage.md](initialiser-garage.md)), reporter les nouvelles clés dans le coffre, puis `make deploy`.
6. Recréer les comptes (Vaultwarden, bibliothèque), réimporter les mots de passe depuis les exports des utilisateurs si elles en ont, redéposer les factures disponibles.

## Vérifier

Les vérifications A1 à A10 du document de travaux pratiques, puis `make backup` et `make restore-test`.

## Après

Le post-mortem doit conclure sur l'action qui aurait évité la perte des données : **une copie des sauvegardes hors de la plateforme** (règle 3-2-1). C'est la première amélioration de la feuille de route.
