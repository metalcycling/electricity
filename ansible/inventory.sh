#!/bin/bash

#
# Create inventory file
#

echo "[renard]" > inventory.ini

renard_ip=$(terraform -chdir=../terraform output -json | jq ".renard_ip.value" | sed 's/"//g')

printf "%-15s  ansible_ssh_private_key_file=key.pri  provider=aws  arch=x86  ansible_user=ubuntu" ${renard_ip} >> inventory.ini
