variable "kubeconfig_path" {
  description = "Path to the kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Kubeconfig context to use (e.g. the kind cluster)"
  type        = string
  default     = "kind-demo"
}

variable "namespace" {
  description = "Namespace to create for the demo app"
  type        = string
  default     = "demo"
}

variable "app_env" {
  description = "Application environment name"
  type        = string
  default     = "ci"
}

variable "app_version" {
  description = "Application version label"
  type        = string
  default     = "0.1.0"
}
