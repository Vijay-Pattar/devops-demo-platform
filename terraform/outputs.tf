output "namespace" {
  description = "The namespace created for the demo app"
  value       = kubernetes_namespace.demo.metadata[0].name
}

output "config_map_name" {
  description = "Name of the app ConfigMap"
  value       = kubernetes_config_map.demo_config.metadata[0].name
}
