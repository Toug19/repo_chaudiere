from PyP100 import PyP110
from sys import argv
import time

# Configuration des informations de connexion
IP_ADDRESS = "192.168.1.152"
EMAIL = "toug31@gmail.com"
PASSWORD = "se6cy9ph"

def connect_to_device(retries=4, delay=2):
    p110 = PyP110.P110(IP_ADDRESS, EMAIL, PASSWORD)

    for attempt in range(retries):
        try:
            p110.handshake()
            p110.login()
            return p110
        except Exception as e:
            # print(f"Failed to connect (attempt {attempt+1}/{retries}). Error: {e}")
            time.sleep(delay)  # Attendre un peu avant de réessayer

    raise Exception("Failed to connect after several attempts.")

def get_data(function_name):
    p110 = connect_to_device()

    if function_name == "getDeviceInfo":
        return p110.getDeviceInfo()
    elif function_name == "getEnergyUsage":
        return p110.getEnergyUsage()
    elif function_name == "turnOn":
        p110.turnOn()
        return "Device turned on"
    elif function_name == "turnOff":
        p110.turnOff()
        return "Device turned off"
    else:
        print(f"Function '{function_name}' is not recognized.")
        exit(1)

def turn_on_socket():
    get_data("turnOn")

def turn_off_socket():
    get_data("turnOff")

if __name__ == "__main__":
    if len(argv) < 2 or len(argv) > 3:
        print("Usage: python get_tapo_data.py <function_name> [key]")
        exit(1)

    function_name = argv[1]

    # Pour les fonctions turnOn et turnOff, aucun second paramètre n'est nécessaire
    if function_name in ["turnOn", "turnOff"]:
        result = get_data(function_name)
        print(result)
    else:
        # Pour getDeviceInfo et getEnergyUsage, un second paramètre est requis
        if len(argv) != 3:
            print(f"Usage: python get_tapo_data.py {function_name} <key>")
            exit(1)

        key = argv[2]

        # Obtenir les données de la fonction
        data = get_data(function_name)

        # Extraire la clé spécifique
        value = data.get(key, None)

        if value is not None:
            print(value)
        else:
            print(f"Key '{key}' not found in the result of {function_name}.")
