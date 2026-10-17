# infra-pme

![CI](https://github.com/paullechevallier99-web/infra-pme/actions/workflows/ci.yml/badge.svg)

Infrastructure d'hébergement d'un cabinet d'expertise comptable de 25 salariés,
entièrement décrite par code : gestionnaire de mots de passe, application de
dépôt de factures, supervision, sauvegardes chiffrées et restauration testée.

Projet réalisé dans le cadre de l'épreuve E6 du BTS SIO.

## Contexte métier

Le cabinet Anonyme Expertise traite les données de 300 clients. Aujourd'hui, les
mots de passe circulent dans un tableur, les pannes sont découvertes par les
utilisateurs et les sauvegardes n'ont jamais été testées. Ce projet répond à ces
problèmes avec une infrastructure reproductible, observée et restaurable.

| Exigence | Objectif |
|---|---|
| Perte de données maximale (RPO) | 24 heures |
| Remise en service (RTO) | 1 heure |
| Détection d'une panne | Moins de 5 minutes |
| Reconstruction | Toute l'infrastructure recréable depuis ce dépôt |

## Architecture cible

Cinq VM Debian 13 sur la plateforme Proxmox de l'école :

| VM | Rôle |
|---|---|
| admin | Bastion d'administration : Git, Terraform, Ansible |
| edge | Point d'entrée HTTPS (Traefik) |
| apps | Vaultwarden, application factures, PostgreSQL, Redis |
| obs | Supervision : Prometheus, Grafana, Loki, Alertmanager |
| backup | Stockage des sauvegardes (Garage, compatible S3) |

## Avancement

- [x] Application factures (API, worker, métriques Prometheus)
- [x] Intégration continue : vérification, scan de vulnérabilités, publication de l'image
- [x] PKI interne et coffre de secrets chiffré (Ansible Vault)
- [ ] Rôles Ansible et tests Molecule
- [ ] Création des VM avec Terraform
- [ ] Supervision et alertes
- [ ] Sauvegardes et test de restauration automatisé
- [ ] Exercice de reprise après sinistre chronométré

## Technologies

Terraform, Ansible, Docker Compose, Proxmox VE, Traefik, PostgreSQL, Redis,
Vaultwarden, Garage, restic, Prometheus, Grafana, Loki, GitHub Actions, Trivy.

## Structure du dépôt

| Dossier | Contenu |
|---|---|
| `app/` | Application factures : API, worker, Dockerfile |
| `ansible/` | Configuration des VM : rôles, inventaire, secrets chiffrés |
| `terraform/` | Création des VM sur Proxmox |
| `pki/` | Autorité de certification interne (clés chiffrées) |
| `docs/` | Documentation, décisions d'architecture, procédures |
| `.github/workflows/` | Intégration continue |

## Tester l'application en local

Prérequis : Docker et le plugin Compose.

```bash
cd app
docker compose -f compose.dev.yml up -d --build
curl http://localhost:8000/healthz
```

## Sécurité

Aucun secret n'est stocké en clair dans ce dépôt : les mots de passe et les clés
privées sont chiffrés avec Ansible Vault. Chaque image est analysée avec Trivy
avant publication, et sa construction échoue si une vulnérabilité grave
corrigeable est détectée.
EOF
