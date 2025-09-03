#!/bin/bash

#
# Generate bills for the apartments
#
# Usage: ./billing.sh <house> <month> <year> <watts> <dollars>
#
# Example: ./billing.sh 8510 march 2025 2450.0 104.88
#

set -e

# Setup

source ${HOME}/.venv/research/bin/activate

rm -f template/.total.txt

# Global variables

declare -A houses

houses["8510"]="apt_101 apt_102 apt_103 apt_104 services"
houses["2260"]="apt_101 apt_102 apt_103 apt_104 services"

# Parse inputs

house=${1}
month=${2}
year=${3}
total_consumption=${4}
total_payment=${5}
price=$(python3 -c "print(f\"{${total_payment} / ${total_consumption}:.4f}\")")

# Generate bills

for unit in ${houses[${house}]}
do
    echo "Generating the bill for '${house}/${unit}'..."

    python3 consumption.py ${house} ${month} ${year} ${unit}

    cd template

    if [[ ${unit} == "apt_101" ]]; then
        name="Apartamento 101"

    elif [[ ${unit} == "apt_102" ]]; then
        name="Apartamento 102"

    elif [[ ${unit} == "apt_103" ]]; then
        name="Apartamento 103"

    elif [[ ${unit} == "apt_104" ]]; then
        name="Estudio"

    elif [[ ${unit} == "services" ]]; then
        name="Services"

    fi

    sed "s/<UNIT>/${name}/g" .bill.tex |
    sed "s/<MONTH>/$(cat .month.dat)/g" |
    sed "s/<YEAR>/${year}/g" |
    sed "s/<ENERGY>/$(cat .energy.dat)/g" |
    sed "s/<PRICE>/${price}/g" |
    sed "s/<PAYMENT>/$(python3 -c "print(f\"{${price} * $(cat .energy.dat):.2f}\")")/g" > bill.tex

    payment=$(python3 -c "print(f\"{${price} * $(cat .energy.dat):.2f}\")")

    echo "${payment} $(cat .energy.dat)" >> .total.txt

    pdflatex bill
    pdflatex bill

    cd ..

    mkdir -p bills/${month}_${year}/${house}
    mv template/bill.pdf bills/${month}_${year}/${house}/${unit}.pdf

    if [[ ${unit} == "apt_104" ]]; then
        mv bills/${month}_${year}/${house}/${unit}.pdf bills/${month}_${year}/${house}/studio.pdf
    fi

    echo
done

# Print total

charge_total=$(python3 -c "import numpy as np; print(f\"{np.loadtxt(\"template/.total.txt\")[:4, 0].sum():.2f}\");")

echo "Total: ${charge_total}"
echo "-----------------------"

month_totals=$(python3 -c "import numpy as np; print(f\"{np.loadtxt(\"template/.total.txt\").sum(axis=0).round(2)}\"[1:-1]);")

echo "Bill: $(echo "${month_totals}" | awk '{ print $1 }')"
echo "Wattage: $(echo "${month_totals}" | awk '{ print $2 }')"

# End of script
