# Grafana

variable grafana_url {
  description = "URL for the Grafana dashboard"
  type = string
  default = "http://54.82.53.86:3000/"
}

variable grafana_token {
  description = "Service account token"
  type = string
  default = "glsa_S40C8gGwv3kvrx5iJk77XQq9XxQgE1TW_2f529369"
}
