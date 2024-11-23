import asyncio
from hoymiles_wifi.dtu import DTU
from google.protobuf.json_format import MessageToDict
import pprint
import csv,os
from datetime import datetime

# script à lancer periodiquement, toute les 5 minuetes par example. avec cron
#genere 2 fichiers:
# 1 fichier avec les reponses brut du module python hoymiles wifi (requete async_get_real_data_new)
# 1 fichier formatte CSV avec toutes les donnes avec application des facteur
# les facteurs ont été trouvé dans https://github.com/suaveolent/hoymiles-wifi/issues/42

CSV_FILE_PATH = "/home/pi/repo_chaudiere/pi-chaudiere/hoymiles-wifi/PV_data.csv"
RESPONSE_FILE = "/home/pi/repo_chaudiere/pi-chaudiere/hoymiles-wifi/response.log"

process_tbd = {
    'sgsData': [  # Correspond à la clé 'sgsData' des données brutes
        {'voltage': 0.1},
        {'frequency': 0.01},
        {'activePower': 0.1},
        {'temperature': 0.1},
        {'serialNumber': None},  # Pas de facteur pour serialNumber
        {'modulationIndexSignal': None}
    ],
    'pvData': [  # Correspond à la clé 'pvData' des données brutes
        {'portNumber': None},
        {'serialNumber': None},  # Pas de facteur pour serialNumber
        {'energyTotal': 1},
        {'energyDaily': 1},
        {'power': 0.1}
    ]
}

async def main():
    ip_address = "192.168.1.155"
    dtu = DTU(ip_address)
    try:
        response = await dtu.async_get_real_data_new()
        if response:
            write_data(str(response) + '\n')
            response_dict = MessageToDict(response)
            return response_dict
        else:
            print("Unable to get response!")
    except Exception as e:
        print(f"An error occurred: {e}")

def process_raw_values(raw_values_dict):
    processed_data = {}

    # Variables pour les totaux
    total_ac_power = 0
    total_dc_power = 0
    total_dc_energy_daily = 0
    total_dc_energy_total = 0

    # Parcourir les sections définies dans process_tbd
    for section, fields in process_tbd.items():
        raw_section_data = raw_values_dict.get(section, [])
        if raw_section_data:  # Vérifier si la section existe dans les données brutes
            processed_section = []

            # Parcourir les données brutes de cette section
            for raw_entry in raw_section_data:
                processed_entry = {}

                # Appliquer les transformations
                for field in fields:
                    for key, factor in field.items():
                        if key in raw_entry:
                            raw_value = raw_entry[key]
                            processed_entry[key] = raw_value * factor if factor else raw_value

                            # Calculer les totaux si applicable
                            if section == 'sgsData' and key == 'activePower' and factor:
                                total_ac_power += raw_value * factor
                            if section == 'pvData':
                                if key == 'power' and factor:
                                    total_dc_power += raw_value * factor
                                elif key == 'energyDaily' and factor:
                                    total_dc_energy_daily += raw_value * factor
                                elif key == 'energyTotal' and factor:
                                    total_dc_energy_total += raw_value * factor

                processed_section.append(processed_entry)

            # Ajouter la section transformée aux données traitées
            processed_data[section] = processed_section

    # Calculer le rendement de l'onduleur
    inverter_yield = (
        total_ac_power / total_dc_power if total_dc_power > 0 else None
    )

    # Ajouter les totaux calculés
    processed_data['totalACPower'] = total_ac_power
    processed_data['totalDCPower'] = total_dc_power
    processed_data['totalDCEnergyDaily'] = total_dc_energy_daily
    processed_data['totalDCEnergyTotal'] = total_dc_energy_total
    processed_data['inverterYield'] = inverter_yield
    processed_data['timestamp'] = raw_values_dict.get('timestamp', None)

    return processed_data

def write_data(data, filename=RESPONSE_FILE):
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
       file.write(data)

def write_csv(processed_data, filename=CSV_FILE_PATH):
    # Créer les en-têtes
    headers = ['timestamp_raw', 'timestamp_readable']

    # Extraire les colonnes dynamiques
    for section, entries in processed_data.items():
        if isinstance(entries, list):  # S'il s'agit de données multi-niveaux
            for i, entry in enumerate(entries):
                for key in entry:
                    headers.append(f"{section}_{key}_{i}")
        else:  # Pour les totaux et autres valeurs simples
            if section != 'timestamp':
                headers.append(section)

    # Créer les données pour le fichier
    timestamp_raw = processed_data.get('timestamp')
    timestamp_readable = (
        datetime.fromtimestamp(timestamp_raw).strftime("%Y-%m-%d %H:%M:%S")
        if timestamp_raw else None
    )
    row = [timestamp_raw, timestamp_readable]

    for section, entries in processed_data.items():
        if isinstance(entries, list):
            for entry in entries:
                row.extend(entry.values())
        elif section != 'timestamp':
            row.append(entries)

    # Écrire le fichier CSV
    file_exists = os.path.exists(filename)  # Vérifier si le fichier existe
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Écrire l'en-tête si le fichier est vide ou nouvellement créé
        if not file_exists or os.stat(filename).st_size == 0:
            writer.writerow(headers)

        # ecrire les nouvelles donnees
        writer.writerow(row)

if __name__ == "__main__":
    raw_values_dict = asyncio.run(main())
    pprint.pprint(raw_values_dict)
    print("traitement")
    processed_values_dict = process_raw_values(raw_values_dict)
    pprint.pprint(processed_values_dict)

    # Exporter les données vers un fichier CSV
    write_csv(processed_values_dict)
    print("Fichier CSV généré :" + CSV_FILE_PATH)

