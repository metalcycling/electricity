#!/bin/bash

#
# Rename AWS node
#

renard_ip=$(terraform -chdir=../terraform output -json | jq ".renard_ip.value" | sed 's/"//g')

if [[ ! "${renard_ip}" == "null" ]]; then
    ssh -o StrictHostKeyChecking=no -i key.pri ubuntu@${renard_ip} sudo hostnamectl set-hostname renard
fi
