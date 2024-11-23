# -*- coding: utf-8 -*-
from PyP100 import PyP110
from sys import argv
import time
import csv
from datetime import datetime

# Configuration des informations de connexion
IP_ADDRESS = "192.168.1.152"
EMAIL = "toug31@gmail.com"
PASSWORD = "se6cy9ph"

# Chemin du fichier de log
LOG_FILE = "/home/pi/log_charge.csv"

# Seuil de courant en watts (a ajuster selon vos besoins)
CURRENT_THRESHOLD = 5  # Exemple de seuil

def log_action(action, result=""):
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, result])

def connect_to_device(retries=4, delay=2):
    p110 = PyP110.P110(IP_ADDRESS, EMAIL, PASSWORD)
    for attempt in range(retries):
        try:
            p110.handshake()
            p110.login()
            return p110
        except Exception as e:
            time.sleep(delay)  # Attendre avant de réessayer
    raise Exception("Failed to connect after several attempts.")

def get_data(function_name):
    p110 = connect_to_device()
    if function_name == "getDeviceInfo":
        result = p110.getDeviceInfo()
        log_action(function_name)
        return result
    elif function_name == "getEnergyUsage":
        result = p110.getEnergyUsage()
        log_action(function_name)
        return result
    elif function_name == "turnOn":
        p110.turnOn()
        log_action(function_name, "Device turned on")
        return "Device turned on"
    elif function_name == "turnOff":
        p110.turnOff()
        log_action(function_name, "Device turned off")
        return "Device turned off"
    else:
        print(f"Function {function_name} is not recognized.")
        exit(1)

def check_and_toggle_power(threshold=CURRENT_THRESHOLD):
    # Vérifier si la prise est allumée
    device_info = get_data("getDeviceInfo")
    if device_info["device_on"]:
        # Récupérer la puissance actuelle
        energy_usage = get_data("getEnergyUsage")
        current_power = energy_usage.get("current_power", 0)

        # Vérifier si la puissance est en dessous du seuil
        if current_power < threshold:
            print("Current power below threshold. Toggling device off and on.")
            log_action("check_and_toggle_power", f"Current power {current_power}W below threshold {threshold}W")
            
            # Éteindre la prise
            get_data("turnOff")
            time.sleep(120)  # Attendre 2 minutes
            # Rallumer la prise
            get_data("turnOn")

if __name__ == "__main__":
    if len(argv) < 2 or len(argv) > 3:
        print("Usage: python tapo_manager.py <function_name> [key]")
        exit(1)

    function_name = argv[1]

    if function_name == "check_and_toggle_power":
        check_and_toggle_power()
    elif function_name in ["turnOn", "turnOff"]:
        result = get_data(function_name)
        print(result)
    else:
        if len(argv) != 3:
            print(f"Usage: python tapo_manager.py {function_name} <key>")
            exit(1)

        key = argv[2]
        data = get_data(function_name)
        value = data.get(key, None)

        if value is not None:
            print(value)
            log_action(function_name, f"{key}: {value}")
        else:
            print(f"Key '{key}' not found in the result of {function_name}.")
            log_action(function_name, f"{key} not found")
