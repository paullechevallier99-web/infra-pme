# L'intégration continue est rouge

**Quand l'utiliser :** sur GitHub, l'onglet **Actions** montre un échec (croix rouge), sur `main` ou sur une proposition de Renovate.
**Impact :** aucune nouvelle image n'est publiée. La production n'est pas touchée : elle garde l'image en place.

## 1. Trouver le job en échec

GitHub, onglet **Actions**, l'exécution en rouge, puis le job en rouge, puis l'étape en rouge : le message est à la fin.

| Job | Ce qui échoue | Résolution |
|---|---|---|
| Infrastructure | `yamllint` : indentation, ligne trop longue | Corriger la ligne citée ; `make lint` en local avant de pousser |
| Infrastructure | `ansible-lint` : règle de bonne pratique | Lire la règle citée ; corriger le rôle |
| Infrastructure | `promtool` : règle d'alerte invalide | Corriger l'expression dans `alerts.yml` |
| Infrastructure | `terraform fmt` ou `validate` | `terraform fmt` dans `terraform/`, puis commiter |
| Dockerfile | `hadolint` | Corriger l'instruction citée |
| Tests | Un des tests `pytest` | Une règle d'extraction est cassée : lire le test, corriger le code |
| Image | **Trivy** : faille HIGH ou CRITICAL corrigeable | Mettre à jour le paquet ou la bibliothèque en cause (`apt-get upgrade` déjà dans le Dockerfile ; version dans `requirements.txt`) |
| Image | Construction impossible | Dépendance introuvable, version inexistante |

## 2. Une proposition de Renovate est rouge

C'est le rôle de la CI : la mise à jour casse quelque chose. **Ne pas fusionner.** Lire l'erreur : soit corriger le code pour accepter la nouvelle version, soit fermer la proposition. Exemple vécu : Python 3.15 bloqué, car Ansible ne le prenait pas en charge.

## 3. Ne jamais contourner

Pas de désactivation du scan, pas de `--exit-code 0`, pas de fusion « pour voir ». Une image vulnérable bloquée est exactement le service attendu.

## Vérifier

Après correction et `git push` : toutes les coches vertes, et une nouvelle image sur GHCR, étiquetée par l'identifiant du commit.
