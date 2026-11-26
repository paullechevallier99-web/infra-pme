# Un déploiement Ansible échoue

**Quand l'utiliser :** `make deploy` (ou `ansible-playbook`) s'arrête avec `failed`, `UNREACHABLE` ou une erreur de déchiffrement.
**Impact :** la VM concernée reste dans l'état où le déploiement s'est arrêté : certains changements appliqués, d'autres non. Les services déjà lancés continuent en général.

## 1. Lire le message

Le récapitulatif (`PLAY RECAP`) donne la VM ; la tâche en rouge juste au-dessus donne la cause.

| Message | Cause | Résolution |
|---|---|---|
| `UNREACHABLE` | Connexion SSH impossible | [acces-ssh-impossible.md](acces-ssh-impossible.md) ; souvent la clé non chargée (`ssh-add ~/.ssh/homelab`) |
| Bloqué sur « Attendre la connexion SSH » | Idem, ou VM neuve encore au démarrage | Charger la clé ; attendre cloud-init |
| `Attempting to decrypt but no vault secrets found` | Mot de passe du coffre introuvable | `echo $ANSIBLE_VAULT_PASSWORD_FILE` ; le fichier `~/.ansible/vault_pass_homelab` existe-t-il ? |
| `vault-ids default,default` | Mot de passe fourni deux fois | Ne pas ajouter `--vault-password-file` : la variable d'environnement suffit |
| `Decryption failed` | Mauvais mot de passe du coffre | Comparer avec la copie dans Bitwarden |
| `'xxx' is undefined` | Variable manquante (souvent un secret pas encore dans le coffre) | Ajouter la variable (`ansible-vault edit`), relancer |
| Erreur dans une tâche `apt` | Dépôt de paquets injoignable, ou verrou apt (mises à jour automatiques en cours) | Attendre et relancer ; tester l'accès à Internet depuis la VM |
| Erreur dans `docker_compose_v2` | Image introuvable (mauvaise version), ou conteneur qui ne démarre pas | Lire le message ; vérifier la version dans `versions.yml` ; `docker compose logs` sur la VM |
| Erreur de syntaxe YAML ou Jinja | Fichier modifié récemment | `make lint` ; `git diff` pour voir la modification |

## 2. Relancer seulement la VM concernée

```
cd ~/infra-pme/ansible
ansible-playbook playbooks/site.yml --limit [vm]
```

Ansible est idempotent : relancer ne refait que ce qui manque.

## 3. Si l'erreur vient d'une modification récente

```
cd ~/infra-pme && git log --oneline -5 && git diff HEAD~1 --stat
```

Annuler la modification (`git revert [commit]`), redéployer, puis corriger à froid.

## Vérifier

Deux passages de suite :

```
ansible-playbook playbooks/site.yml --limit [vm]
ansible-playbook playbooks/site.yml --limit [vm] | tail -5      # changed=0, failed=0
```
