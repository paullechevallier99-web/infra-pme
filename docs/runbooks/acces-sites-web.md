# Les sites ne s'ouvrent pas dans le navigateur

**Quand l'utiliser :** la bibliothèque des factures, Vaultwarden ou Grafana ne s'affichent pas dans ton navigateur, alors que tu n'as reçu aucune alerte.
**Impact :** variable : souvent un problème du poste, pas de l'infrastructure.

## 1. Situer le problème : serveur ou poste ?

Depuis la VM admin :

```
curl -s https://factures.lab.internal/healthz; echo
curl -s -o /dev/null -w "vault : %{http_code}\n" https://vault.lab.internal/alive
curl -s -o /dev/null -w "grafana : %{http_code}\n" https://grafana.lab.internal/api/health
```

- **Tout répond** (`{"status":"ok"}`, `200`, `200`) : les services fonctionnent, le problème est **entre ton poste et edge** : suite de cette fiche.
- **Rien ne répond** : problème côté serveur : [service-probe-failed.md](service-probe-failed.md).

## 2. Le navigateur ne trouve pas le site

| Message du navigateur | Cause | Résolution |
|---|---|---|
| `ERR_NAME_NOT_RESOLVED` | Le nom `*.lab.internal` n'est pas connu du poste | Ajouter dans le fichier `hosts` (Windows : `C:\Windows\System32\drivers\etc\hosts`, ouvert en administrateur) : `172.31.19.2 vault.lab.internal factures.lab.internal grafana.lab.internal` |
| `ERR_CONNECTION_TIMED_OUT` | Le poste ne joint pas `172.31.19.2` | Hors de l'école : [acces-distant-tailscale.md](acces-distant-tailscale.md), point 3 ; à l'école : vérifier le réseau du poste (Wi-Fi invité ?) |
| `ERR_PROXY_CONNECTION_FAILED` | Navigateur lancé avec le proxy, mais tunnel fermé | Relancer `ssh -D 1080 -N ops@100.88.14.33` |
| Avertissement de sécurité (`NET::ERR_CERT_AUTHORITY_INVALID`) | La CA interne n'est pas installée sur ce poste | Installer `pki/ca.crt` comme autorité racine de confiance (vérifier l'empreinte SHA-1 `9C:EE:1B:A0:...`) |
| `NET::ERR_CERT_DATE_INVALID` | Certificat expiré | [renouveler-certificat.md](renouveler-certificat.md) |
| Fenêtre de connexion qui revient en boucle (bibliothèque) | Mauvais identifiant ou mot de passe | Compte `comptable`, mot de passe dans Bitwarden ; tester depuis la VM admin : `curl -s -n -o /dev/null -w "%{http_code}" https://factures.lab.internal/factures?limit=1` doit répondre `200` |
| `401` ou `429` | Mot de passe refusé, ou limite de débit atteinte | Attendre quelques secondes pour le `429` ; vérifier le mot de passe pour le `401` |

## 3. Profil de navigateur séparé

Lancé avec `--user-data-dir`, Chrome ouvre un profil **vierge** : pas de mots de passe enregistrés, pas d'extension, et la CA doit être installée dans le magasin **Windows** (pas seulement dans Firefox) pour être reconnue. Copier le mot de passe depuis Bitwarden.

## Vérifier

Les trois sites s'ouvrent avec le cadenas, sans avertissement.
