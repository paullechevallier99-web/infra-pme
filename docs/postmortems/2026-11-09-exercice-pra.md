# Exercice de PRA : perte de la VM apps

Date : 9 novembre 2026. Type : exercice planifié.
Résumé : destruction volontaire de la VM apps, puis reconstruction et restauration.
Durée totale : 6 min 06 s, pour un objectif (RTO) de 60 min. Aucune perte de données.

## Chronologie (heure UTC de la VM admin)

| Heure | Événement |
|---|---|
| 12:52:03 | Dernière sauvegarde (snapshot 91865f8e), contenant 3 factures de test |
| 12:52:36 | Début : `terraform apply -replace` sur la VM apps |
| 12:53:02 | VM recréée en 26 s ; début de la reconfiguration Ansible |
| 12:58:02 | VM reconfigurée, services vides (« Facture inconnue ») ; début de la restauration |
| 12:58:42 | Données restaurées ; 3 factures retrouvées, Vaultwarden opérationnel |

## Ce qui a bien fonctionné

- La reconstruction entièrement depuis le dépôt Git : Terraform puis Ansible, sans intervention manuelle.
- La restauration ciblée d'un snapshot précis, grâce à l'identifiant passé à `restore-prod.sh`.
- L'isolement de la VM backup : les sauvegardes ont survécu à la perte de la VM apps.

## Ce qui a mal fonctionné (lors de la première tentative)

- La clé `homelab` n'était pas chargée dans l'agent SSH : Ansible a attendu jusqu'à interruption.
- Un snapshot trop ancien, antérieur au dépôt des factures, a d'abord été restauré : les données
  semblaient perdues jusqu'à la restauration du bon snapshot.
- Les VM n'étaient pas toutes sur le même fuseau horaire, ce qui a compliqué la lecture des heures.

## Actions correctives

| Action | État |
|---|---|
| Vérifier `ssh-add -l` dans les prérequis du runbook de restauration | À faire |
| Lister les snapshots et choisir celui qui précède immédiatement l'incident | À faire |
| Afficher le nombre de factures restaurées dans `restore-prod.sh` | À faire |
| Passer la VM admin au fuseau Europe/Paris | À faire |
