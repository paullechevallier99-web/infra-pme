# Alertes InvoiceQueueBacklog et ClassementDegrade

**Quand l'utiliser :**
- `InvoiceQueueBacklog` : plus de 50 factures en attente dans la file, depuis 10 minutes.
  Le worker est arrêté, bloqué, ou trop lent.
- `ClassementDegrade` : plus de la moitié des factures de la dernière heure sont « à vérifier »
  (sur au moins 5), depuis 15 minutes. Nouveau modèle de facture, PDF scannés, ou régression.

**Gravité :** avertissement. Les factures ne sont pas perdues : elles attendent, ou elles sont
rangées dans `a_verifier/`.

## 1. InvoiceQueueBacklog : le worker traite-t-il ?

Sur apps :

    sudo docker compose -f /opt/apps/compose.yml ps worker redis
    sudo docker compose -f /opt/apps/compose.yml logs --tail 50 worker

| Constat | Résolution |
|---|---|
| Worker arrêté ou `Restarting` | Ses journaux donnent l'erreur ; relancer : `sudo docker compose -f /opt/apps/compose.yml up -d worker` |
| Erreurs répétées `erreur sur [id]` | Erreur de traitement : base, fichier introuvable ; lire le message |
| Worker actif, file qui diminue | Simple pic de dépôts : attendre |

## 2. ClassementDegrade : pourquoi « à vérifier » ?

Dans Grafana (Explore, Loki) :

    {container="apps-worker-1"} |= "à vérifier"

| Information manquante | Cause | Que faire |
|---|---|---|
| `texte` | PDF scannés, sans texte | Classement manuel ; l'OCR n'est pas prise en charge |
| `siret`, `date` ou `montant` | Format de facture inhabituel | Ajouter la règle dans `app/worker/extraction.py`, avec un test |
| Toutes les factures, depuis un déploiement | Régression | Revenir à l'image précédente (`factures_version`), déployer apps |

Après une nouvelle image : réanalyser les factures concernées, depuis la bibliothèque
(bouton **Réanalyser**) ou par `POST /factures/[id]/reanalyser`.

## 3. Vérifier

La file redescend (`factures_queue_length` dans Grafana) ; le taux de classement remonte dans le
tableau de bord **Application factures** ; `[RESOLVED]` sur Discord.
