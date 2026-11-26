# Alerte CertificateExpiringSoon : renouveler le certificat

**Quand l'utiliser :** le certificat `*.lab.internal` expire dans moins de 21 jours.
**Gravité :** avertissement. À l'expiration, les navigateurs refuseront les sites, et les
applications (Bitwarden) refuseront de se connecter.

La CA (valable 10 ans) ne change pas : seul le certificat du serveur est renouvelé. Rien n'est
à réinstaller sur les postes.

## 1. Vérifier la date actuelle

    openssl x509 -in ~/infra-pme/pki/wildcard.crt -noout -subject -enddate

## 2. Créer le nouveau certificat

Sur la VM admin. La clé de la CA est le secret le plus sensible : elle n'est déchiffrée que le
temps de signer, dans un fichier temporaire, effacé ensuite.

    cd ~/infra-pme/pki
    ansible-vault decrypt --output /tmp/ca.key ca.key
    openssl req -newkey rsa:2048 -nodes -keyout /tmp/wildcard.key -out /tmp/wildcard.csr -subj "/CN=*.lab.internal"
    printf "subjectAltName=DNS:*.lab.internal,DNS:lab.internal\n" > /tmp/san.ext
    openssl x509 -req -in /tmp/wildcard.csr -CA ca.crt -CAkey /tmp/ca.key -CAcreateserial \
      -out wildcard.crt -days 397 -sha256 -extfile /tmp/san.ext
    ansible-vault encrypt --output wildcard.key /tmp/wildcard.key
    shred -u /tmp/ca.key /tmp/wildcard.key /tmp/wildcard.csr /tmp/san.ext
    rm -f ca.srl

Vérifier :

    openssl x509 -in wildcard.crt -noout -subject -issuer -enddate
    head -1 wildcard.key        # $ANSIBLE_VAULT;1.1;AES256

## 3. Déployer

    cd ~/infra-pme/ansible && ansible-playbook playbooks/site.yml --limit edge

## 4. Vérifier, puis enregistrer

    curl -sv https://vault.lab.internal/alive 2>&1 | grep "expire date"
    cd ~/infra-pme && git status       # seuls wildcard.crt et wildcard.key modifiés
    git add pki/wildcard.crt pki/wildcard.key
    git commit -m "chore(pki): renouvellement du certificat *.lab.internal"
    git push

**Vérifier avant le commit** que `wildcard.key` commence bien par `$ANSIBLE_VAULT` : une clé privée
en clair dans Git serait compromise.
