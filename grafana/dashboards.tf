# Folders

resource "grafana_folder" "management" {
  title = "Management"
}

resource "grafana_folder" "apt_101" {
  title = "Apartment 101"
}

resource "grafana_folder" "apt_102" {
  title = "Apartment 102"
}

resource "grafana_folder" "apt_103" {
  title = "Apartment 103"
}

resource "grafana_folder" "apt_104" {
  title = "Apartment 104"
}

# Dashboards

resource "grafana_dashboard" "management" {
  for_each = fileset("${path.module}/management", "*.json")
  config_json = file("${path.module}/management/${each.key}")
  folder = grafana_folder.management.id
}

resource "grafana_dashboard" "apt_101" {
  for_each = fileset("${path.module}/apt_101", "*.json")
  config_json = file("${path.module}/apt_101/${each.key}")
  folder = grafana_folder.apt_101.id
}

resource "grafana_dashboard" "apt_102" {
  for_each = fileset("${path.module}/apt_102", "*.json")
  config_json = file("${path.module}/apt_102/${each.key}")
  folder = grafana_folder.apt_102.id
}

resource "grafana_dashboard" "apt_103" {
  for_each = fileset("${path.module}/apt_103", "*.json")
  config_json = file("${path.module}/apt_103/${each.key}")
  folder = grafana_folder.apt_103.id
}

resource "grafana_dashboard" "apt_104" {
  for_each = fileset("${path.module}/apt_104", "*.json")
  config_json = file("${path.module}/apt_104/${each.key}")
  folder = grafana_folder.apt_104.id
}
