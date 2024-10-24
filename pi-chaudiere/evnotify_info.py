import requests
import json
from datetime import datetime

# Variables pour AKEY et TOKEN (remplace par tes vraies valeurs)
AKEY = '2165c6'  # Replace with your actual AKEY
TOKEN = '0f532b415bb7cb05b4bf'  # Replace with your actual TOKEN
ADDRESS = f"https://app.evnotify.de/soc?akey={AKEY}&token={TOKEN}"

# Fonction pour obtenir le SOC actuel depuis l'API
def get_soc_display():
    response = _fetch_data()
    if response:
        value = response.get('soc_display', None)
        if value is None:
            return "soc_display value not found"
        return value
    return "Error fetching data"

# Fonction pour obtenir la date unix de la dernière lecture du SOC
def get_last_soc():
    response = _fetch_data()
    if response:
        value = response.get('last_soc', None)
        if value is None:
            return "last_soc value not found"
        return value  #retourne la date unix timestamp
    return "Error fetching data"


# Fonction pour obtenir le dernier SOC sous une forme lisible
def get_last_soc_readable():
    response = _fetch_data()
    if response:
        last_soc_value = response.get('last_soc', None)
        if last_soc_value is None:
            return "last_soc value not found"
        
        # Convertir le timestamp en format lisible
        readable_date = datetime.fromtimestamp(last_soc_value)
        formatted_date = readable_date.strftime("le %d %B %Y à %H heures %M")
        return formatted_date
    return "Error fetching data"

# Fonction privée pour récupérer les données de l'API
def _fetch_data():
    try:
        response = requests.get(ADDRESS)
        response.raise_for_status()  # Raise an error if the request failed
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête: {e}")
        return None
