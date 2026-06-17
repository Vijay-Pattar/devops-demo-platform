terraform {
  required_version = ">= 1.5.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.31"
    }
  }
}

# Points at whatever kubeconfig is active (e.g. the kind cluster created in CI).
provider "kubernetes" {
  config_path    = var.kubeconfig_path
  config_context = var.kube_context
}

# A dedicated namespace for the demo app, managed as code.
resource "kubernetes_namespace" "demo" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/part-of" = "devops-demo-platform"
      "managed-by"                = "terraform"
    }
  }
}

# A ConfigMap demonstrating config-as-code delivered alongside the app.
resource "kubernetes_config_map" "demo_config" {
  metadata {
    name      = "demo-app-config"
    namespace = kubernetes_namespace.demo.metadata[0].name
  }
  data = {
    APP_ENV     = var.app_env
    LOG_LEVEL   = "info"
    APP_VERSION = var.app_version
  }
}
