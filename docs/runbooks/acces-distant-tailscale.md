# L'accès à distance par Tailscale ne fonctionne plus

**Quand l'utiliser :** depuis l'extérieur de l'école, impossible de joindre la VM admin (`100.88.14.33`), Proxmox (`100.79.210.24`), ou les sites `*.lab.internal`.
**Impact :** plus d'administration à distance. Depuis le réseau de l'école, tout reste accessible.

## 1. Identifier ce qui ne passe pas

| Symptôme | Aller à |
|---|---|
| `ssh ops@100.88.14.33` : délai dépassé | 2 |
| SSH vers la VM admin fonctionne, mais pas les sites web | 3 |
| Proxmox (`100.79.210.24`) injoignable | 4 |
| Le jury ne peut pas se connecter | [acces-jury.md](acces-jury.md) |

## 2. La VM admin est injoignable par Tailscale

Sur ton PC :

```
tailscale status
```

| Constat | Cause | Résolution |
|---|---|---|
| Tailscale arrêté sur le PC | Application fermée, déconnectée | Relancer l'application, se reconnecter |
| La machine `admin` absente de la liste | Le PC est sur un autre réseau Tailscale (autre compte) | Changer de compte dans l'application (`tailscale switch`) |
| `admin` présente mais `offline` | Tailscale arrêté sur la VM admin, ou VM éteinte | Depuis l'école ou la console Proxmox : `sudo systemctl status tailscaled`, puis `sudo tailscale up` si déconnectée |
| `admin` en ligne, SSH refusé | Pare-feu UFW de la VM admin | Console : `sudo ufw status` doit autoriser le port 22 sur `tailscale0` |

**Ne jamais lancer `tailscale up` avec une seule option** sur une machine déjà configurée : cette commande réinitialise tous les réglages non précisés (étiquette, routes). Pour modifier un réglage : `tailscale set`.

## 3. Les sites web ne répondent pas depuis chez toi

Les sites sont sur le VLAN 19 (`172.31.19.2`), que ton PC ne joint pas directement. Deux chemins possibles :

**a. La route Tailscale** : la VM admin annonce le VLAN 19.

```
# sur la VM admin
tailscale debug prefs | grep -i -A3 advertiseroutes      # doit contenir 172.31.19.0/24
```

Si `null` : `sudo tailscale set --advertise-routes=172.31.19.0/24`, puis dans la console Tailscale, **Machines**, `admin`, **⋯**, **Edit route settings**, cocher la route. Sur le PC : `tailscale debug prefs | Select-String RouteAll` doit afficher `true` (option **Use Tailscale subnets**).

Test sur le PC (PowerShell) : `Test-NetConnection 172.31.19.2 -Port 443` doit indiquer `InterfaceAlias : Tailscale`. Si c'est `Wi-Fi`, la route n'est pas active.

**b. Le proxy SOCKS** : toujours disponible, sans aucune configuration.

```
ssh -D 1080 -N ops@100.88.14.33
"C:\Program Files\Google\Chrome\Application\chrome.exe" --proxy-server="socks5://localhost:1080" --user-data-dir="%TEMP%\chrome-admin"
```

Test sans navigateur : `curl.exe -sk --socks5-hostname localhost:1080 https://factures.lab.internal/healthz`.

## 4. Proxmox injoignable par Tailscale

`proxmox-acces` est une machine **partagée par l'école** (réseau de Jimmy). Si elle est absente ou `offline` dans `tailscale status`, le problème est de son côté : le signaler à l'enseignant. Depuis l'école, Proxmox reste accessible à `https://172.31.114.1:8006`.

## Vérifier

```
ssh ops@100.88.14.33 hostname                    # admin
curl.exe -sk https://factures.lab.internal/healthz   # si la route Tailscale est active
```

## Recours

Si Tailscale est indisponible : travailler depuis le réseau de l'école (`ssh ops@172.31.19.1`), ou utiliser la console Proxmox.
