# %% Modules

import os
import json
import time
import threading

from pyemvue import PyEmVue
from pyemvue.enums import Scale, Unit

from flask import Flask
from prometheus_client import make_wsgi_app, Gauge
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask(__name__)

# %% Connect to Emporia to gather data

vue = PyEmVue()

if os.path.exists("keys.json"):
    with open("keys.json") as fileptr:
        data = json.load(fileptr)

    vue.login(
        id_token = data["id_token"],
        access_token = data["access_token"],
        refresh_token = data["refresh_token"],
        token_storage_file = "keys.json",
    )
else:
    try:
        vue.login(
            username = os.environ["ELECTRICITY_USERNAME"],
            password = os.environ["ELECTRICITY_PASSWORD"], 
            token_storage_file = "keys.json"
        )
    except KeyError as e:
        raise KeyError(f"Missing required environment variable: {str(e)}")

# %% Collect devices available

devices = vue.get_devices()
devices_gids = []
devices_info = {}

for device in devices:
    if not device.device_gid in devices_gids:
        devices_gids.append(device.device_gid)
        devices_info[device.device_gid] = device

    else:
        devices_info[device.device_gid].channels += device.channels

devices_not_needed = [409289, 409297, 409305, 409325]

for device_gid in devices_not_needed:
    devices_gids.remove(device_gid)
    devices_info.pop(device_gid)

# %% Data aggregation for each apartment

meters = {
    "8510": {
        "apt_101": {
                     "fridge": (403928, "14"),
                    "kitchen": (403928, "13"),
                  "microwave": (403928, "15"),
                      "stove": (403928, "16"),
                "multi_use_8": (403928, "11"),
                "multi_use_7": (403928, "12"),
        },

        "apt_102": {
                     "fridge": (403089, "2"),
                  "microwave": (403089, "3"),
                      "stove": (403089, "1"),
                "multi_use_3": (403089, "4"),
                "multi_use_1": (403089, "5"),
        },

        "apt_103": {
                     "fridge": (403089, "15"),
                  "microwave": (403089, "14"),
                      "stove": (403089, "16"),
                "multi_use_5": (403089, "12"),
                "multi_use_2": (403089, "13"),
            "air_conditioner": (403089, "6"),
        },

        "apt_104": {
                     "fridge": (403928, "4"),
                  "microwave": (403928, "2"),
                      "stove": (403928, "1"),
                   "bathroom": (403928, "5"),
                  "multi_use": (403928, "3"),
        },

        "services": {
                  "ac_unit_1": (403868, "3"),
                  "ac_unit_2": (403868, "4"),
                  "ac_unit_3": (403868, "13"),
                  "ac_unit_4": (403868, "12"),
                     "washer": (403868, "14"),
               "water_heater": (403868, "97"),
                      "dryer": (403868, "98"),
        },
    },

    "2260": {
        "apt_101": {
                 "unit_101_a": (481856, "15"),
                 "unit_101_b": (481856, "16"),
        },

        "apt_102": {
                 "unit_102_a": (481856, "1"),
                 "unit_102_b": (481856, "2"),
        },

        "apt_103": {
                 "unit_103_a": (481856, "13"),
                 "unit_103_b": (481856, "14"),
        },

        "apt_104": {
                 "unit_104_a": (481856, "3"),
                 "unit_104_b": (481856, "4"),
        },

        "services": {
                    "laundry": (481856, "97"),
            "air_conditioner": (481856, "98"),
               "water_heater": (481856, "99"),
        },
    },

    "1641": {
        "apt_102": {
                 "unit_102_a": (516941, "16"),
                 "unit_102_b": (516941, "15"),
        },

        "apt_103": {
                 "unit_103_a": (516941, "14"),
                 "unit_103_b": (516941, "13"),
        },

        "services": {
                   "laundry_a": (516941, "1"),
                   "laundry_b": (516941, "2"),
        },
    },
}

# %% Functions to gather data

def get_usage_data(devices_gids):
    """
    Read usage data across all devices
    """
    return vue.get_device_list_usage(
        deviceGids=devices_gids,
        instant=None,
        scale=Scale.SECOND.value,
        unit=Unit.KWH.value
    )

def read_meter(property, apartment, circuit, device_usage):
    """
    Get 'circuit' meter data for 'apartment'
    """
    device_id = meters[property][apartment][circuit][0]
    circuit_id = meters[property][apartment][circuit][1]

    return device_usage[device_id].channels[circuit_id].usage * (3600 * 1000.0)

# %% Set metrics to be collected with Prometheus

atlantis_watts = Gauge("atlantis_watts", "Instantaneous watts being consumed", ["meter", "circuit"])
roja_watts = Gauge("roja_watts", "Instantaneous watts being consumed", ["meter", "circuit"])
hacienda_watts = Gauge("hacienda_watts", "Instantaneous watts being consumed", ["meter", "circuit"])

# %% Set the metric value periodically

def update_metrics():
    """
    Update the value of the metric
    """
    frequency = 2

    while True:
        try:
            device_usage = get_usage_data(devices_gids)

            for property in meters:
                for meter, circuits in meters[property].items():
                    for circuit in circuits:
                        watts = read_meter(property, meter, circuit, device_usage)

                        if property == "8510":
                            atlantis_watts.labels(meter=meter, circuit=circuit).set(watts)

                        elif property == "2260":
                            roja_watts.labels(meter=meter, circuit=circuit).set(watts)

                        elif property == "1641":
                            hacienda_watts.labels(meter=meter, circuit=circuit).set(watts)

        except Exception as e:
            print(f"Error updating metrics: {e}")

        time.sleep(frequency)

thread = threading.Thread(target=update_metrics, daemon=True)
thread.start()

# %% Expose application end point

@app.route("/")
def home():
    return "Metrics are exposed at /metrics."

# %% Expose the metrics endpoint

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    "/metrics": make_wsgi_app()
})

# %% Main program

if __name__ == "__main__":
    app.run(port=9091)

# %% End of script
