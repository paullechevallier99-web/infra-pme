variable "proxmox_endpoint" {
  description = "Adresse de l'interface Proxmox de l'école"
  type        = string
}

variable "node_name" {
  description = "Nœud Proxmox sur lequel créer les VM"
  type        = string
}

variable "pool_id" {
  description = "Pool (espace) attribué par l'école"
  type        = string
}

variable "template_id" {
  description = "Identifiant du modèle Debian 13 compatible cloud-init"
  type        = number
}

variable "datastore_id" {
  description = "Stockage des disques"
  type        = string
}

variable "bridge" {
  description = "Pont réseau"
  type        = string
}

variable "vlan_id" {
  description = "VLAN attribué, ou null s'il n'y en a pas"
  type        = number
  default     = null
}

variable "gateway" {
  description = "Passerelle du sous-réseau attribué"
  type        = string
}

variable "dns_servers" {
  description = "Serveurs DNS de l'école"
  type        = list(string)
}

variable "disk_interface" {
  description = "Interface du disque du modèle (onglet Matériel dans Proxmox)"
  type        = string
  default     = "scsi0"
}

variable "ssh_public_key_file" {
  description = "Clé publique déposée sur chaque VM pour l'utilisateur ops"
  type        = string
  default     = "~/.ssh/homelab.pub"
}

variable "extra_admin_keys" {
  description = "Clés publiques supplémentaires (poste de la salle, PC personnel)"
  type        = list(string)
  default     = []
}

variable "vms" {
  description = "VM à créer : identifiant, adresse IP et ressources"
  type = map(object({
    id   = number
    ip   = string
    cpu  = number
    mem  = number # en Mo
    disk = number # en Go
  }))

  validation {
    condition     = contains(keys(var.vms), "backup")
    error_message = "La VM backup doit exister : elle contient les sauvegardes."
  }
}
