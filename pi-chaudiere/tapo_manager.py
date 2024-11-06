from PyP100 import PyP110
from sys import argv
import time
import csv
from datetime import datetime

# Configuration des informations de connexion
IP_ADDRESS = "192.168.1.152"
EMAIL = "toug31@gmail.com"
PASSWORD = "se6cy9ph"

# Nom du fichier de log
LOG_FILE = "/home/pi/log_charge.csv"

def log_action(action, result=""):
    # Ajoute une ligne dans le fichier de log avec la date, l'heure et l'action effectuée
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
            time.sleep(delay)  # Attendre un peu avant de réessayer

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
        print(f"Function '{function_name}' is not recognized.")
        exit(1)

if __name__ == "__main__":
    if len(argv) < 2 or len(argv) > 3:
        print("Usage: python tapo_manager.py <function_name> [key]")
        exit(1)

    function_name = argv[1]

    # Pour les fonctions turnOn et turnOff, aucun second paramètre n'est nécessaire
    if function_name in ["turnOn", "turnOff"]:
        result = get_data(function_name)
        print(result)
    else:
        # Pour getDeviceInfo et getEnergyUsage, un second paramètre est requis
        if len(argv) != 3:
            print(f"Usage: python tapo_manager.py {function_name} <key>")
            exit(1)

        key = argv[2]

        # Obtenir les données de la fonction
        data = get_data(function_name)

        # Extraire la clé spécifique
        value = data.get(key, None)

        if value is not None:
            print(value)
            log_action(function_name, f"{key}: {value}")
        else:
            print(f"Key '{key}' not found in the result of {function_name}.")
            log_action(function_name, f"{key} not found")
