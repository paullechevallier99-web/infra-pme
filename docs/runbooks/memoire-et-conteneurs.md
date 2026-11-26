# Alertes MemoryPressure et ContainerRestarting

**Quand l'utiliser :**
- `MemoryPressure` : plus de 90 % de mémoire utilisée, depuis 10 minutes. Les VM n'ont pas de swap :
  à court de mémoire, le noyau tue un processus.
- `ContainerRestarting` : un conteneur a redémarré plus de 2 fois en 15 minutes. Docker le relance
  seul (`restart: unless-stopped`) : sans cette alerte, un plantage en boucle passerait inaperçu.

**Gravité :** avertissement.

## 1. MemoryPressure : qui consomme ?

Sur la VM concernée :

    free -h
    sudo docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"
    sudo journalctl -k | grep -i "out of memory" | tail -5

| Constat | Résolution |
|---|---|
| Un conteneur anormalement gros | Ses journaux (`docker compose logs`) ; le relancer |
| « out of memory » dans le journal | Un processus a été tué : vérifier les services (`docker ps`) |
| Consommation durablement haute | Augmenter `mem` dans `ecole.auto.tfvars`, `terraform apply`, puis arrêter et démarrer la VM dans Proxmox |

## 2. ContainerRestarting : pourquoi plante-t-il ?

Le message indique le conteneur et la VM. Sur cette VM :

    sudo docker ps -a --format "{{.Names}}  {{.Status}}"
    sudo docker logs --tail 50 [conteneur]
    sudo docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}}' [conteneur]

| Constat | Cause |
|---|---|
| `OOMKilled` à `true` | Limite de mémoire du conteneur dépassée (voir la partie 1) |
| Erreur de configuration dans les journaux | Modification manuelle, ou mauvais secret : redéployer la VM |
| Erreur de connexion à la base ou à Redis | Ces services sont-ils démarrés ? |

## 3. Vérifier

Le conteneur reste `Up` plus de 15 minutes, et `[RESOLVED]` sur Discord.
