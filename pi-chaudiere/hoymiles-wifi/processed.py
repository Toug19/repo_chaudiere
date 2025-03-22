import asyncio
from hoymiles_wifi.dtu import DTU
from google.protobuf.json_format import MessageToDict
import pprint

process_tbd = {
    'sgsData': [  # Correspond à la clé 'sgsData' des données brutes
        {'voltage': 0.1},
        {'frequency': 0.01},
        {'activePower': 0.1},
        {'temperature': 0.1},
        {'serialNumber': None},  # Pas de facteur pour serialNumber
        {'modulationIndexSignal': None}  # Exemple champ supplémentaire
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
            #print("Protobuf Response (raw):")
            #print(response)

            # Convertir l'objet Protobuf en dictionnaire ou JSON
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
                            # Appliquer le facteur ou conserver la valeur brute
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

    return processed_data





if __name__ == "__main__":
    raw_values_dict=asyncio.run(main())
    pprint.pprint(raw_values_dict)
    print("traitement")
    processed_values_dict = process_raw_values(raw_values_dict)
    pprint.pprint(processed_values_dict)

