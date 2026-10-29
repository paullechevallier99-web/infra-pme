.PHONY: help lint check plan-deploy deploy-initial deploy backup restore-test test

help: ## Affiche cette aide
	@grep -E '^[a-z-]+:.*## ' Makefile | sed 's/:.*## /\t/'

lint: ## Vérifie tous les fichiers YAML et les rôles Ansible
	yamllint -d relaxed .
	cd ansible && ansible-lint

check: ## Vérifie la syntaxe du playbook principal
	cd ansible && ansible-playbook playbooks/site.yml --syntax-check

plan-deploy: ## Montre ce que le déploiement changerait, sans rien modifier
	cd ansible && ansible-playbook playbooks/site.yml --check --diff

deploy-initial: ## Premier déploiement, sans les sauvegardes (avant l'initialisation de Garage)
	cd ansible && ansible-playbook playbooks/site.yml --skip-tags sauvegardes

deploy: ## Déploie toute l'infrastructure
	cd ansible && ansible-playbook playbooks/site.yml

backup: ## Lance une sauvegarde immédiate sur la VM apps
	cd ansible && ansible apps -b -m ansible.builtin.systemd_service -a "name=restic-backup.service state=started"

restore-test: ## Lance un test de restauration sur la VM apps
	cd ansible && ansible apps -b -m ansible.builtin.systemd_service -a "name=restic-restore-test.service state=started"

test: ## Lance les tests Molecule de tous les rôles (long)
	set -e; for r in common docker edge apps garage backup agents observability; do \
	  (cd ansible/roles/$$r && molecule test); \
	done


plan: ## Montre les VM que Terraform créerait ou modifierait
	cd terraform && terraform plan

up: ## Crée ou met à jour les VM
	cd terraform && terraform apply

rebuild: ## Détruit et recrée edge, apps et obs, puis les reconfigure (jamais backup)
	cd terraform && terraform apply $(foreach vm,$(REBUILDABLE),-replace='proxmox_virtual_environment_vm.vm["$(vm)"]')
	$(MAKE) deploy
