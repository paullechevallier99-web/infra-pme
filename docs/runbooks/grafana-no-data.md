# Grafana affiche « No data » ou des panneaux vides

**Quand l'utiliser :** un tableau de bord ou une recherche dans l'Explore ne montre rien.
**Impact :** aucun sur les services ; c'est souvent un problème de lecture, pas une panne.

| Constat | Cause | Résolution |
|---|---|---|
| L'Explore est vide | Aucune requête saisie | Choisir la source, écrire une requête (`up`), cliquer sur **Run query** |
| « No data » sur le tableau de bord de l'application, sauf la file d'attente à 0 | Aucune facture déposée depuis le dernier redémarrage de l'application : ses compteurs n'existent qu'après le premier événement | Déposer quelques factures ; les panneaux se remplissent en une minute |
| Tous les panneaux vides | La période affichée est trop ancienne ou trop courte | En haut à droite : **Last 24 hours** |
| Erreur sur la source de données | Source ajoutée à la main avec une mauvaise adresse | Utiliser les sources `Prometheus` et `Loki` créées au déploiement (adresses `http://prometheus:9090` et `http://loki:3100`) ; supprimer les autres |
| « No data » pour une seule VM | Ses agents ne répondent plus | Prometheus, cible `DOWN` : [instance-down.md](instance-down.md) |
| Aucun journal d'une VM dans Loki | Alloy arrêté ou bloqué sur cette VM | `sudo docker logs --tail 20 agents-alloy-1` sur la VM ; relancer `/opt/agents` |
| Tout est vide, partout | Prometheus ou Loki arrêtés | [supervision-hors-service.md](supervision-hors-service.md) |

## Vérifier

Dans l'Explore : `sum by (host) (up)` (source Prometheus) affiche les 4 VM ; `{source="journal"}` (source Loki) affiche des lignes.
