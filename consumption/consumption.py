# %% Modules

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from scipy.integrate import cumulative_trapezoid

from datetime import datetime

from prometheus_api_client import PrometheusConnect

from months import *

# %% Check command line arguments

assert len(sys.argv) >= 5, "Not enough arguments: consumption.py <house> <month> <year> <unit> (<day>)"

house = sys.argv[1]
month = sys.argv[2]
year  = sys.argv[3]
meter = sys.argv[4]
day   = 1 if len(sys.argv) == 5 else int(sys.argv[5])

assert meter in ["apt_101", "apt_102", "apt_103", "apt_104", "services"], "ERROR: Wrong unit provided"

# %% Connect to database

prometheus_url = "http://54.82.53.86:9090"
prometheus = PrometheusConnect(url = prometheus_url)

# %% Functions

def get_consumption(house, meter, start, end):
    """
    Get power consumption data in kWh from 'start' to 'end'

    Args:
    - house (str): House to bill
    - meter (str): Meter to query
    - start (str): Start time
    - end (str): End time
    """

    times = {
        "start": datetime.fromisoformat(start),
        "end": datetime.fromisoformat(end),
    }

    assert times["end"] > times["start"], "The start time is greater or equal to the end time"

    # Divide data query in to segements of 'num_days' days to avoid overloading the server

    num_days = 5
    period_seconds = num_days * (24 * 3600)

    intervals = [times["start"].timestamp()]

    while intervals[-1] < times["end"].timestamp():
        intervals.append(min(intervals[-1] + period_seconds, times["end"].timestamp()))

    # Get data for each interval

    consumption = {
        "power": {},
        "energy": {},
    }

    for idx in range(len(intervals) - 1):
        if house == "8510":
            query = "atlantis_watts{meter=\"%s\"}[%ds] @ %f" % (
                meter,
                int(intervals[idx + 1] - intervals[idx]),
                intervals[idx + 1],
            )

        elif house == "2260":
            query = "roja_watts{meter=\"%s\"}[%ds] @ %f" % (
                meter,
                int(intervals[idx + 1] - intervals[idx]),
                intervals[idx + 1],
            )

        elif house == "1641":
            query = "hacienda_watts{meter=\"%s\"}[%ds] @ %f" % (
                meter,
                int(intervals[idx + 1] - intervals[idx]),
                intervals[idx + 1],
            )

        circuits = prometheus.custom_query(query)

        if len(circuits) == 0:
            continue

        for circuit in circuits:
            if circuit["metric"]["circuit"] in consumption["power"]:
                consumption["power"][circuit["metric"]["circuit"]].append(np.array(circuit["values"], dtype = float))
            else:
                consumption["power"][circuit["metric"]["circuit"]] = [np.array(circuit["values"], dtype = float)]

        if house == "8510" and (meter == "apt_101" or meter == "apt_102"):
            if meter == "apt_101":
                query = "atlantis_watts{meter=\"services\",circuit=~\"ac_unit_3|ac_unit_4\"}[%ds] @ %f" % (
                    int(intervals[idx + 1] - intervals[idx]),
                    intervals[idx + 1],
                )
            else:
                query = "atlantis_watts{meter=\"services\",circuit=~\"ac_unit_1|ac_unit_2\"}[%ds] @ %f" % (
                    int(intervals[idx + 1] - intervals[idx]),
                    intervals[idx + 1],
                )
    
            ac_circuits = prometheus.custom_query(query)

            if "ac" in consumption["power"]:
                consumption["power"]["ac"].append(np.zeros((len(ac_circuits[0]["values"]), len(ac_circuits))))
            else:
                consumption["power"]["ac"] = [np.zeros((len(ac_circuits[0]["values"]), len(ac_circuits)))]

            for ac_circuit in ac_circuits:
                consumption["power"]["ac"][-1] += np.array(ac_circuit["values"], dtype = float)

            consumption["power"]["ac"][-1][:, 0] /= len(ac_circuits)

        elif house == "8510" and meter == "services":
            for circuit in ["ac_unit_1", "ac_unit_2", "ac_unit_3", "ac_unit_4"]:
                consumption["power"].pop(circuit)

    num_samples = 0

    for circuit in consumption["power"]:
        consumption["power"][circuit] = np.vstack(consumption["power"][circuit])

        if consumption["power"][circuit].shape[0] > num_samples:
            num_samples = consumption["power"][circuit].shape[0]
            reference_circuit = circuit

    for circuit in consumption["power"]:
        if consumption["power"][circuit].shape[0] < num_samples:
            num_missing = num_samples - consumption["power"][circuit].shape[0]
            consumption["power"][circuit] = np.vstack([np.zeros((num_missing, 2)), consumption["power"][circuit]])
            consumption["power"][circuit][:num_missing, 0] = consumption["power"][reference_circuit][:num_missing, 0]

    consumption["power"]["total"] = np.array([measurements for circuit, measurements in consumption["power"].items()]).sum(axis = 0)
    consumption["power"]["total"][:, 0] /= len(consumption["power"]) - 1

    for circuit, measurements in consumption["power"].items():
        consumption["energy"][circuit] = np.vstack((
            measurements[:, 0],
            cumulative_trapezoid(measurements[:, 1], measurements[:, 0] / 3600.0, initial = 0.0) / 1.0e3
        )).T

    return consumption, (times["end"] - times["start"]).days

start = f"{year}-{months[month]['number'] + 0:02d}-{day:02d}T00:00:00+00:00"
end   = f"{year}-{months[month]['number'] + 1:02d}-01T00:00:00+00:00" if month != "december" else f"{int(year) + 1}-{months['january']['number']:02d}-01T00:00:00+00:00"

consumption, num_days = get_consumption(house, meter, start, end)

for circuit, measurements in consumption["energy"].items():
    print(circuit, measurements[-1, -1])

# %% Generate consumption graph

data = consumption["energy"]["total"]
timestamps = data[:, 0]
energy = data[:, 1]

dates = pd.to_datetime(timestamps, unit="s")

df = pd.DataFrame({"date": dates, "energy": energy})

df["day"] = df["date"].dt.date
daily_energy = df.groupby("day")["energy"].agg(lambda x: x.iloc[-1] - x.iloc[0])

accumulated_energy = daily_energy.cumsum()

# %% Plot setup

label_size = 16
title_size = 18
ticks_size = 14
legend_size = 15

fig, ax1 = plt.subplots(figsize = (15, 7))

# Bar chart for daily energy consumption

ax1.bar(daily_energy.index, daily_energy.values, color = "cornflowerblue", alpha = 1.0, label = "Consumo energetico diario", zorder = 3)
ax1.set_xlabel("Date", fontsize = label_size)
ax1.set_ylabel("Kilovatios-hora (kWh)", fontsize = label_size, color = "royalblue")
ax1.tick_params(axis = "y", labelcolor = "royalblue", labelsize = ticks_size)
ax1.tick_params(axis = "x", labelsize = ticks_size)
ax1.grid(axis = "y", linestyle = "--", alpha = 0.7)

# Secondary y-axis for accumulated energy

ax2 = ax1.twinx()
ax2.plot(daily_energy.index, accumulated_energy, color = "darkred", marker = "o", linestyle = "-", linewidth = 2, label = "Consumo energetico accumulado")
ax2.set_ylabel("Kilovatios-hora (kWh)", fontsize = label_size, color = "darkred")
ax2.tick_params(axis = "y", labelcolor = "darkred", labelsize = ticks_size)

# Set xticks and rotate labels

ax1.set_xticks(daily_energy.index)
ax1.set_xticklabels(daily_energy.index, rotation = 45, ha = "right", fontsize = ticks_size)

# Title and legend with larger font

plt.title(f"Consumo energetico del mes de {months[month]['name']} del {year}", fontsize = title_size)
fig.tight_layout()
ax1.legend(loc = "upper left", prop = {"size":legend_size}, bbox_to_anchor = (0.0, 1.0))
ax2.legend(loc = "upper left", prop = {"size":legend_size}, bbox_to_anchor = (0.0, 0.93))

# %% Save data

plt.savefig("template/.consumption.pdf", bbox_inches = "tight")

with open("template/.energy.dat", "w") as fileptr:
    fileptr.write(f"{consumption['energy']['total'][-1, -1]:.2f}")

with open("template/.num_days.dat", "w") as fileptr:
    fileptr.write(f"{num_days}")

with open("template/.month.dat", "w") as fileptr:
    fileptr.write(f"{months[month]['name']}")

# %% End of script
