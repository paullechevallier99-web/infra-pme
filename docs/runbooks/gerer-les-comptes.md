# Gérer les comptes des services

**Quand l'utiliser :** créer, changer ou supprimer un accès à la bibliothèque des factures, à Grafana ou à Vaultwarden.

## Bibliothèque des factures (authentification de Traefik)

Les comptes sont dans `vault_factures_basicauth` (coffre), sous la forme `nom:empreinte_bcrypt`, un par ligne. Pour ajouter ou changer un mot de passe :

```
docker run --rm httpd:2.4-alpine htpasswd -nbB [nom] '[mot de passe]'
cd ~/infra-pme/ansible
ansible-vault edit inventories/lab/group_vars/all/vault.yml     # ajouter ou remplacer la ligne
ansible-playbook playbooks/site.yml --limit edge
```

Le mot de passe en clair ne doit être conservé que dans Bitwarden. Pour la VM admin, mettre à jour `~/.netrc` (droits 600) si le compte `comptable` change.

**Vérifier :** `curl -s -n -o /dev/null -w "%{http_code}\n" "https://factures.lab.internal/factures?limit=1"` doit répondre `200`, et `401` sans `-n`.

## Grafana

- Mot de passe administrateur : `vault_grafana_admin_password`. Il n'est lu qu'à la **création** de Grafana ; pour le changer ensuite :

  ```
  ssh -i ~/.ssh/homelab ops@172.31.19.4 "sudo docker exec obs-grafana-1 grafana cli admin reset-admin-password '[nouveau]'"
  ```

  puis mettre la même valeur dans le coffre, pour qu'une reconstruction d'obs le conserve.
- Autres comptes (jury, lecture seule) : dans Grafana, **Administration**, **Users**, **New user**, avec le rôle voulu (*Viewer*, *Editor*, *Admin*).

## Vaultwarden

Voir [vaultwarden.md](vaultwarden.md) : invitations, jeton d'administration, mot de passe maître perdu.

## Supprimer un accès

Retirer la ligne du coffre (bibliothèque) puis déployer edge ; supprimer l'utilisateur dans Grafana ou dans la page d'administration de Vaultwarden. Pour un départ du cabinet : changer aussi les mots de passe partagés qu'il connaissait.
