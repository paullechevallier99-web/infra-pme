# Initialiser Garage

**Quand :** une seule fois, après le premier déploiement du rôle `garage`.
**Où :** sur la VM `backup` (`ssh backup` depuis le poste de la salle).
**Pourquoi :** Garage refuse de stocker des données tant que son organisation
(le « layout ») n'est pas définie. Le seau et la clé de restic doivent aussi
être créés à la main.

## Étapes

1. Repérer l'identifiant du nœud (première colonne) :

       sudo docker exec garage /garage status

2. Déclarer le nœud et sa capacité, puis appliquer :

       sudo docker exec garage /garage layout assign -z dc1 -c 15G <ID_DU_NOEUD>
       sudo docker exec garage /garage layout apply --version 1

3. Créer le seau des sauvegardes :

       sudo docker exec garage /garage bucket create restic

4. Créer la clé d'accès de restic. **Noter le Key ID et le Secret key affichés** :

       sudo docker exec garage /garage key create restic-key

5. Autoriser cette clé sur ce seau uniquement :

       sudo docker exec garage /garage bucket allow --read --write --owner restic --key restic-key

## Vérification

    sudo docker exec garage /garage bucket info restic

La section `KEYS FOR THIS BUCKET` doit afficher la clé `restic-key` avec les droits `RWO`.

## Après l'initialisation

1. Ranger le Key ID et le Secret key dans le coffre, depuis la VM `admin` :

       cd ~/infra-pme/ansible
       ansible-vault edit inventories/lab/group_vars/all/vault.yml

   Remplacer `vault_restic_s3_key_id` et `vault_restic_s3_secret`.
   Ne jamais copier ces valeurs ailleurs (messages, captures, documents).
2. Commiter le coffre, puis redéployer le rôle `backup` sur la VM `apps`.

## Pièges connus

- `--key restic-key` s'écrit d'un seul tenant, avec un tiret.
- `sudo` est nécessaire : l'utilisateur `ops` n'est pas dans le groupe `docker`.
- La syntaxe peut varier d'une version majeure de Garage à l'autre :
  `sudo docker exec garage /garage --help` liste les commandes disponibles.
