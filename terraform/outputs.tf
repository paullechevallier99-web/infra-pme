output "vm_ips" {
  description = "Adresse IP de chaque VM créée"
  value       = { for name, vm in var.vms : name => vm.ip }
}
