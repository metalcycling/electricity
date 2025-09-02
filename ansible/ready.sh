#!/bin/bash

#
# Wait for nodes to be ready for SSH
#

set -e

renard_ip=$(terraform -chdir=../terraform output -json | jq ".renard_ip.value" | sed 's/"//g')

while [[ ! "${renard_ip}" == "null" ]]
do
    echo "Waiting for renard..."

    set +e

    response=$(ssh -o ConnectTimeout=1 -o StrictHostKeyChecking=no -o BatchMode=yes ${renard_ip} 2>&1 | grep "Permission denied")

    if [[ $? = 0 ]]; then
        break
    fi

    set -e

    sleep 5
done
