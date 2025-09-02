#!/bin/bash

#
# Builder configuration management script
#

set -e

# Wait for nodes to be ready for SSH

bash ready.sh

# Rename nodes

bash rename.sh

# Create inventory file

bash inventory.sh

# Check the state of the infrastructure

ansible-playbook check.yaml

# Run actions separated by ','

actions=${1:-"packages,root"}

for action in $(echo ${actions} | tr ',' '\n')
do
    if [[ ${action} == "packages" ]]; then
        ansible-playbook packages.yaml

    elif [[ ${action} == "root" ]]; then
        ansible-playbook root.yaml

    elif [[ ${action} == "prometheus" ]]; then
        ansible-playbook prometheus.yaml

    elif [[ ${action} == "grafana" ]]; then
        ansible-playbook grafana.yaml

    elif [[ ${action} == "application" ]]; then
        ansible-playbook application.yaml

    else
        echo "Nothing to do"

    fi
done
