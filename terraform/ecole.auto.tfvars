# Valeurs d'exemple : à remplacer par celles de docs/environnement-ecole.md
proxmox_endpoint = "https://pve.bts.lan:8006/"
node_name        = "pve2"
pool_id          = "sio2-paul"
template_id      = 9013
datastore_id     = "local-lvm"
bridge           = "vmbr0"
vlan_id          = 60
gateway          = "192.168.60.254"
dns_servers      = ["192.168.60.254"]

vms = {
  edge   = { id = 2310, ip = "192.168.60.10", cpu = 1, mem = 1024, disk = 10 }
  apps   = { id = 2320, ip = "192.168.60.20", cpu = 2, mem = 2048, disk = 20 }
  obs    = { id = 2330, ip = "192.168.60.30", cpu = 2, mem = 2048, disk = 20 }
  backup = { id = 2340, ip = "192.168.60.40", cpu = 1, mem = 1024, disk = 40 }
}
