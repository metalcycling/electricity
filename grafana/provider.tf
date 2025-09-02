# Grafana

provider "grafana" {
  url = var.grafana_url
  auth = var.grafana_token
}
