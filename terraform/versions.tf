terraform {
  required_version = ">= 1.10"

  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.95" # remplacer par la version trouvée à l'étape 1
    }
  }
}

provider "proxmox" {
  endpoint = var.proxmox_endpoint
  # Certificat auto-signé de la plateforme de l'école : voir l'ADR 0011
  insecure = true
  # Le jeton d'API est lu dans la variable d'environnement PROXMOX_VE_API_TOKEN
}
