# Valeurs d'exemple : à remplacer par celles de docs/environnement-ecole.md
proxmox_endpoint = "https://172.31.114.1:8006/"
node_name        = "pve-3"
pool_id          = "paul.l"
template_id      = 120
datastore_id     = "local-lvm"
bridge           = "vmbr1"
vlan_id          = 19
gateway          = "172.31.19.254"
dns_servers      = ["9.9.9.9"]

vms = {
  edge   = { id = 996, ip = "172.31.19.2", cpu = 1, mem = 1024, disk = 10 }
  apps   = { id = 997, ip = "172.31.19.3", cpu = 2, mem = 2048, disk = 20 }
  obs    = { id = 998, ip = "172.31.19.4", cpu = 2, mem = 2048, disk = 20 }
  backup = { id = 999, ip = "172.31.19.5", cpu = 1, mem = 1024, disk = 40 }
}
