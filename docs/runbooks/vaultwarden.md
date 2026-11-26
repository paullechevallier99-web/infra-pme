# Vaultwarden : panne, comptes et accès d'administration

**Quand l'utiliser :** Vaultwarden ne répond plus, un utilisateur ne peut pas se connecter, il faut créer un compte, ou la page d'administration refuse le jeton.
**Impact :** les utilisateurs gardent une copie hors ligne de leur coffre dans leur application Bitwarden, mais ne synchronisent plus.

## 1. Vaultwarden ne répond plus

Sur apps :

```
cd /opt/apps
sudo docker compose ps vaultwarden
sudo docker compose logs --tail 40 vaultwarden
```

| Constat | Résolution |
|---|---|
| Arrêté | `sudo docker compose up -d vaultwarden` |
| Erreur sur la base (`database is locked`, `malformed`) | [restauration-partielle.md](restauration-partielle.md), point 4 |
| Disque plein | [disque-plein.md](disque-plein.md) |
| Il tourne, mais le site échoue | Le chemin web : [service-probe-failed.md](service-probe-failed.md) |

## 2. Créer un compte

Les inscriptions sont fermées. Deux façons :

- **Par invitation** : page d'administration `https://vault.lab.internal/admin`, avec le jeton (dans Bitwarden), rubrique **Users**, **Invite user**. Vaultwarden n'envoie pas d'e-mail ici : l'utilisateur crée son compte avec l'adresse invitée.
- **En ouvrant les inscriptions un instant** : `vaultwarden_signups_allowed: true` dans les variables de apps, déployer apps, créer le compte, puis remettre `false` et redéployer.

## 3. La page d'administration refuse le jeton

Le jeton saisi est le **mot de passe en clair** (dans Bitwarden) ; le coffre Ansible n'en contient que le hachage Argon2. Si le mot de passe est perdu, en générer un nouveau :

```
docker run --rm -it vaultwarden/server:[version de versions.yml] /vaultwarden hash
```

Mettre le hachage dans `vault_vaultwarden_admin_token` (`ansible-vault edit`), puis déployer apps. Ranger le nouveau mot de passe dans Bitwarden.

## 4. Un utilisateur a perdu son mot de passe maître

**Impossible à récupérer, par conception** : le coffre est chiffré avec ce mot de passe, que le serveur ne connaît pas. Supprimer son compte depuis la page d'administration, le recréer, et l'utilisateur ressaisit ses mots de passe. C'est la garantie que même l'administrateur ne peut pas lire les coffres.

## Vérifier

```
curl -s -o /dev/null -w "%{http_code}\n" https://vault.lab.internal/alive     # 200
```

et une connexion réussie depuis une application Bitwarden.
