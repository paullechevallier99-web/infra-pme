# Mettre à jour un composant, et revenir en arrière

**Quand l'utiliser :** une proposition de Renovate est verte et tu veux l'appliquer ; ou une nouvelle version de l'application est publiée ; ou une mise à jour vient de casser un service.

## 1. Appliquer une mise à jour d'image (Traefik, Grafana, PostgreSQL…)

1. Lire la proposition : version, notes de version. Une version **majeure** demande ton approbation, et une attention particulière (PostgreSQL : une version majeure change le format des données).
2. Fusionner la proposition sur GitHub.
3. Sur la VM admin :

   ```
   cd ~/infra-pme && git pull
   make backup                                      # avant toute mise à jour de apps
   cd ansible && ansible-playbook playbooks/site.yml --limit [vm] --check --diff
   ansible-playbook playbooks/site.yml --limit [vm]
   ```

4. Vérifier le service, puis surveiller les alertes pendant une heure.

## 2. Déployer une nouvelle version de l'application

1. La CI a publié l'image, étiquetée par les 7 premiers caractères du commit.
2. Mettre cette étiquette dans `factures_version` (`ansible/inventories/lab/group_vars/all/versions.yml`), commiter, pousser.
3. `git pull` sur la VM admin, `make backup`, puis `ansible-playbook playbooks/site.yml --limit apps` : migrations, nouvelle image, conteneurs recréés.
4. Déposer une facture de test, vérifier son classement.

## 3. Revenir en arrière

Le service est cassé depuis la mise à jour :

```
cd ~/infra-pme && git log --oneline -5
git revert [commit de la mise à jour]          # remet l'ancienne version dans versions.yml
git push
cd ansible && ansible-playbook playbooks/site.yml --limit [vm]
```

**Cas particulier des bases de données :** si une nouvelle version a déjà converti les données (version majeure de PostgreSQL), revenir à l'ancienne image ne suffit pas : restaurer aussi la base depuis la sauvegarde faite juste avant ([restauration-partielle.md](restauration-partielle.md)). D'où le `make backup` avant chaque mise à jour.

## Vérifier

Le service répond, l'alerte éventuelle passe à `RESOLVED`, et `ansible-playbook ... --check --diff` affiche `changed=0`.
