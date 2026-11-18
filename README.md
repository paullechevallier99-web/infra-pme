# infra-pme

![CI](https://github.com/paullechevallier99-web/infra-pme/actions/workflows/ci.yml/badge.svg)

Infrastructure d'hébergement d'un cabinet d'expertise comptable, **entièrement décrite par le code** :
gestionnaire de mots de passe, application de classement des factures, supervision avec alertes,
sauvegardes chiffrées et restauration testée chaque semaine.

Projet réalisé pour l'épreuve E6 du BTS SIO, option SISR, sur la plateforme Proxmox de l'école.

## Résultats mesurés

| Mesure | Objectif | Résultat |
|---|---|---|
| Remise en service après la perte totale de la VM apps (RTO) | 1 h | **6 min 06 s** |
| Détection d'une panne (alerte Discord) | 5 min | **moins de 3 min 30 s** |
| Perte de données maximale (RPO) | 24 h | Sauvegarde chaque nuit, test de restauration chaque semaine |
| Reconstruction | Depuis ce dépôt | Les 4 VM recréées par Terraform, configurées par Ansible |
| Images vulnérables bloquées par la CI avant la production | — | 2 (faille système, puis faille d'une bibliothèque) |

Le détail de l'exercice de reprise est dans [`docs/postmortems/2026-11-09-exercice-pra.md`](docs/postmortems/2026-11-09-exercice-pra.md).

## Contexte

Le cabinet Anonyme Expertise (contexte fictif : 25 salariés, 300 clients) n'a pas d'équipe informatique.
Ses mots de passe circulaient dans un tableur, ses factures étaient classées à la main, ses pannes
découvertes par les utilisateurs, et ses sauvegardes n'avaient jamais été testées.

| Besoin | Réponse |
|---|---|
| Gestionnaire de mots de passe en HTTPS | Vaultwarden derrière Traefik |
| Dépôt et classement des factures | API et worker : extraction du SIRET, de la date et du montant, bibliothèque web |
| Être prévenu d'une panne | Prometheus et Alertmanager, alertes sur Discord |
| Consulter les journaux | Loki et Grafana Alloy |
| Isoler les services | Une VM par rôle |
| Ne pas dépendre d'une seule personne | Tout est dans ce dépôt, documenté |

## Architecture

```
Postes de l'école ─┐                         ┌─ edge    172.31.19.2  Traefik : HTTPS, certificat interne
                   ├─ SSH ─ admin (bastion) ─┼─ apps    172.31.19.3  Vaultwarden, factures, PostgreSQL, Redis
Tailscale ─────────┘        172.31.19.1      ├─ obs     172.31.19.4  Prometheus, Alertmanager, Grafana, Loki
                                             └─ backup  172.31.19.5  Garage (S3) : sauvegardes restic
```

| VM | Rôle | Créée par |
|---|---|---|
| admin | Bastion : Git, Terraform, Ansible. Seul point d'entrée de l'administration | À la main, documentée |
| edge | Point d'entrée HTTPS (Traefik) | Terraform |
| apps | Vaultwarden, application factures, PostgreSQL, Redis, sauvegardes | Terraform |
| obs | Supervision : métriques, alertes, tableaux de bord, journaux | Terraform |
| backup | Stockage des sauvegardes, protégé contre la suppression | Terraform |

Sur chaque VM : node_exporter, cAdvisor et Grafana Alloy. Chaque flux réseau autorisé est décrit
dans une matrice, et appliqué par UFW et par la chaîne `DOCKER-USER`.

## Démarrage

Prérequis : une VM admin avec Terraform, Ansible et Docker, un jeton d'API Proxmox, et le mot de passe
du coffre Ansible Vault dans `~/.ansible/vault_pass_homelab`.

```bash
cp terraform/ecole.auto.tfvars.example terraform/ecole.auto.tfvars   # valeurs de la plateforme
export PROXMOX_VE_API_TOKEN="$(cat ~/.proxmox_token)"
make up                  # crée les 4 VM
make deploy-initial      # configure tout, sauf les sauvegardes
# initialiser Garage : docs/runbooks/initialiser-garage.md
make deploy              # déploiement complet
```

| Commande | Effet |
|---|---|
| `make lint` | Vérifie les fichiers YAML, les rôles Ansible et la mise en forme Terraform |
| `make plan-deploy` | Montre ce que le déploiement changerait, sans rien modifier |
| `make deploy` | Déploie toute l'infrastructure |
| `make backup` · `make restore-test` | Lance une sauvegarde, ou un test de restauration |
| `make plan` · `make up` | Terraform : voir, puis appliquer les changements de VM |
| `make rebuild` | Détruit et recrée edge, apps et obs, puis les reconfigure (jamais backup) |
| `make test` | Tests Molecule de tous les rôles |
| `make help` | Liste de toutes les commandes |

## Structure du dépôt

| Dossier | Contenu |
|---|---|
| `terraform/` | Création des VM sur Proxmox (fournisseur bpg/proxmox, cloud-init) |
| `ansible/` | 8 rôles : `common`, `docker`, `agents`, `edge`, `apps`, `garage`, `backup`, `observability` ; inventaire ; secrets chiffrés |
| `app/` | Application factures : API, worker, migrations de la base, tests |
| `pki/` | Autorité de certification interne (clés privées chiffrées) |
| `docs/` | Runbooks et post-mortem |
| `.github/workflows/` | Intégration continue |

## Sécurité

- **Aucun secret en clair** : mots de passe, jetons et clés privées sont chiffrés avec Ansible Vault (AES-256).
  L'historique complet a été vérifié avec gitleaks.
- **SSH par clé uniquement**, root refusé, administration depuis le seul bastion.
- **Pare-feu sur chaque VM**, entrant refusé par défaut, y compris pour les ports publiés par Docker (`DOCKER-USER`).
- **HTTPS partout**, certificat signé par une autorité interne ; l'API exige un mot de passe et limite le débit.
- **Chaîne logicielle** : versions épinglées, mises à jour proposées par Renovate, scan Trivy bloquant
  avant toute publication d'image.

## Intégration continue

À chaque push : analyse des fichiers YAML et des rôles Ansible, vérification des règles d'alerte et de la mise
en forme Terraform, analyse du Dockerfile, tests de l'application, construction de l'image, scan de vulnérabilités,
puis publication sur GitHub Container Registry. Le déploiement reste une décision humaine, depuis le bastion.

## Sauvegardes et reprise

Chaque nuit, la VM apps sauvegarde la base PostgreSQL, Vaultwarden et les factures avec restic, chiffrées et
dédupliquées, vers Garage sur la VM backup. Chaque dimanche, un test restaure automatiquement la dernière
sauvegarde dans un environnement jetable et vérifie son contenu. Une alerte se déclenche si la dernière
sauvegarde réussie a plus de 26 heures.

Procédure de restauration : [`docs/runbooks/restauration.md`](docs/runbooks/restauration.md).

## Limites connues et suite

- **Pas de copie des sauvegardes hors de la plateforme** : une panne de Proxmox emporterait données et sauvegardes.
  Prochaine étape : `restic copy` vers un stockage externe (règle 3-2-1).
- **Pas de haute disponibilité** : la plateforme est un point unique de défaillance, hors de mon contrôle.
- La VM admin est configurée à la main, et le mot de passe du coffre y est stocké dans un fichier.
- Le classement ne lit pas les factures scannées (pas d'OCR) ; elles attendent une vérification manuelle.

## Tester l'application en local

Prérequis : Docker et le plugin Compose.

```bash
cd app
docker compose -f compose.dev.yml up -d --build
curl http://localhost:8000/healthz
```
