resource "proxmox_virtual_environment_vm" "vm" {
  for_each = var.vms

  name      = each.key
  node_name = var.node_name
  vm_id     = each.value.id
  pool_id   = var.pool_id
  tags      = ["terraform", "infra-pme", each.key]
  on_boot   = true

  # La VM de sauvegarde ne peut pas être supprimée par erreur (voir l'ADR 0003)
  protection = each.key == "backup"

  clone {
    vm_id = var.template_id
    full  = true
  }

  # L'agent invité est installé par Ansible : Terraform ne l'attend pas
  agent {
    enabled = false
  }

  cpu {
    cores = each.value.cpu
  }

  memory {
    dedicated = each.value.mem
  }

  disk {
    datastore_id = var.datastore_id
    interface    = var.disk_interface
    size         = each.value.disk
  }

  network_device {
    bridge  = var.bridge
    vlan_id = var.vlan_id
  }

  # cloud-init : adresse IP, DNS, utilisateur ops et clés SSH au premier démarrage
  initialization {
    datastore_id = var.datastore_id

    ip_config {
      ipv4 {
        address = "${each.value.ip}/24"
        gateway = var.gateway
      }
    }

    dns {
      servers = var.dns_servers
    }

    user_account {
      username = "ops"
      keys = concat(
        [trimspace(file(pathexpand(var.ssh_public_key_file)))],
        var.extra_admin_keys,
      )
    }
  }
}
