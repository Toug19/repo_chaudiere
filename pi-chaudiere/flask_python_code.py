# coding: utf-8

from flask import Flask
from flask_ask import Ask, statement, convert_errors
import RPi.GPIO as GPIO
import logging, os, evnotify_info, datetime, re
from crontab import CronTab
from urllib.request import urlopen
from datetime import datetime, timedelta, timezone
import pytz

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

CONSIGNE_FILE='/home/pi/repo_chaudiere/pi-chaudiere/CONSIGNE_TEMPERATURE.txt'
READ_TEMP_URL='http://192.168.1.73'

chauffage_cron_comment = 'Alexa CRON job for heater'
chauffage_cron_command = 'python3 /home/pi/repo_chaudiere/pi-chaudiere/2_PLANCHER_AUTO_GPIO16-PIN36.py >> Logs_Chaudiere_2_PLANCHER.log'
chauffage_cron_period = 15

start_charge_cron_comment = 'Alexa CRON job powering ON the plug'
start_charge_cron_command = 'python3 /home/pi/repo_chaudiere/pi-chaudiere/tapo_manager.py turnOn'

stop_charge_cron_comment = 'Alexa CRON job powering OFF the plug'
stop_charge_cron_command = 'python3 /home/pi/repo_chaudiere/pi-chaudiere/tapo_manager.py turnOff'

charge_daily_comment = 'Alexa CRON job daily powering ON the plug'

my_cron = CronTab(user='pi')

boolean2statement = dict()
boolean2statement[0] = 'éteint'
boolean2statement[1] = 'allumé'

device2gpio=dict()
device2gpio["chaudière"]=40
device2gpio["chauffe eau"]=40
device2gpio["eau chaude"]=40

device2gpio["boucle"]=38
device2gpio["e. c. s. "]=38

device2gpio["plancher"]=36
device2gpio["chauffage"]=36

CAR_BATTERY_SIZE_KWH = float(64)
CAR_CHARGING_SPEED_KW = float(2.7)

PV_info_log_file = '/home/pi/repo_chaudiere/pi-chaudiere/hoymiles-wifi/response.log'
paris_tz = pytz.timezone("Europe/Paris")


# set all gpio as output
for device in device2gpio:
    GPIO.setup(device2gpio[device], GPIO.OUT)

def check_if_alexa_job_exists(cron_job_comment):
    for job in my_cron:
        if job.comment == cron_job_comment:
            return True
    return False

def disable_chauffage_alexa_job(cron_job_comment):
    for job in my_cron:
        if job.comment == cron_job_comment:
            my_cron.remove(job)
            my_cron.write()

def enable_periodic_alexa_job(cron_job_comment, cron_job_command, period):
    job = my_cron.new(command=cron_job_command, comment=cron_job_comment)
    job.minute.every(period)
    my_cron.write()

def enable_alexa_job(cron_job_comment, cron_job_command, date_run):
    job = my_cron.new(command=cron_job_command, comment=cron_job_comment)
    job.setall(date_run)
    my_cron.write()

def read_temperature_on_webpage(url):
	return str(round(float(urlopen(url).read().decode('utf8')), 1))

def process_photovoltaic_data(file_path=PV_info_log_file):
    # Read the file content
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Split readings based on blocks starting with "device_serial_number" and ending with empty lines
    readings = content.strip().split("\n\n")
    
    # Prepare to track results
    power_sums = []
    timestamps = []
    
    # Process each reading
    for reading in readings:
        if "device_serial_number" not in reading:
            continue
        
        # Extract timestamp
        timestamp_match = re.search(r'timestamp:\s*(\d+)', reading)
        timestamp = int(timestamp_match.group(1)) if timestamp_match else None
        if timestamp:
            timestamps.append(timestamp)
        
        # Extract active_power values from sgs_data
        active_powers = [
            int(match.group(1)) * 0.1  # Apply the factor of 0.1
            for match in re.finditer(r'sgs_data\s*{[^}]*?active_power:\s*(\d+)', reading)
        ]
        
        # Sum active powers if they exist, otherwise append 0
        power_sums.append(sum(active_powers) if active_powers else 0)
    
    # Handle cases where no readings are available
    if not power_sums or not timestamps:
        return None, 0, 0, None

    # Analyze the last reading
    last_power_sum = power_sums[-1]
    last_timestamp = timestamps[-1]
    
    # Convert last timestamp to timezone-aware datetime
    last_datetime = datetime.fromtimestamp(last_timestamp, tz=paris_tz)
    
    # Calculate the average of the last 4 readings
    last_4_avg = sum(power_sums[-4:]) / min(4, len(power_sums))
    
    return last_timestamp, last_power_sum, last_4_avg, last_datetime


app = Flask(__name__)
ask = Ask(app, '/')
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

@ask.intent('GetPVInfo')
def get_PV_info():
    last_timestamp, current_power, last_4_avg, last_datetime = process_photovoltaic_data()
    human_last_datetime = format_date(last_datetime)
    return statement(f"La production actuelle est de {str(int(current_power))} watt, la production moyenne de {str(int(last_4_avg))} watt, relevé {human_last_datetime} ")

@ask.intent('AskTemperature')
def ask_temperature():
    return statement('Il fait actuellement {} degrès maintenant dans la maison'.format(read_temperature_on_webpage(READ_TEMP_URL)))


@ask.intent('GPIOControlIntent', mapping={'status': 'status', 'device': 'device'})
def gpio_control(status, device):
    print("Args are:")
    print(" device: " + device)
    print(" status: " + status)
    pin = device2gpio[device]

    try:
        pinNum = int(pin)
    except Exception as e:
        return statement('Pin number not valid.')

    if status in ['on', 'actif']:    GPIO.output(pinNum, GPIO.HIGH)
    if status in ['off', 'inactif']:    GPIO.output(pinNum, GPIO.LOW)

    return statement('Je positionne {} à {}'.format(device, status))

@ask.intent('GPIOStatusIntent')
def gpio_status():
    '''
    This function reads the state of the GPIO, thus status of chaudière and boucle and plancher
    '''
    returned_statement = str()
    previous_device_pin = 0

    for device in device2gpio:
       # Same gpio is listed more than 1 time with different name. 
        if previous_device_pin != device2gpio[device]:
            returned_statement = returned_statement + ' ' + device + ' ' + 'est ' + boolean2statement[GPIO.input(device2gpio[device])] + '.'
        previous_device_pin = device2gpio[device]

    returned_statement = returned_statement + ' Le chauffage est ' + boolean2statement[check_if_alexa_job_exists(chauffage_cron_comment)]
    return statement(returned_statement)

@ask.intent('Chauffage_off')
def chauffage_off():
    if check_if_alexa_job_exists(chauffage_cron_comment) == False:
        return statement("Le chauffage était déja éteint")
    else:
        disable_chauffage_alexa_job(chauffage_cron_comment)
        GPIO.output(device2gpio["plancher"], GPIO.LOW)
        return statement('Chauffage éteint')

@ask.intent('Chauffage_on')
def chauffage_on():
    if check_if_alexa_job_exists(chauffage_cron_comment) == True:
        return statement("Le chauffage était déja allumé")
    else:
        enable_periodic_alexa_job(chauffage_cron_comment, chauffage_cron_command, chauffage_cron_period)
        return statement('Chauffage allumé')
    
@ask.intent('Consigne_request')
def consigne_request():
    consigne_file = open(CONSIGNE_FILE, "r")
    consigne_temperature = float(consigne_file.readline())
    consigne_file.close()
    if check_if_alexa_job_exists(chauffage_cron_comment) == True:
        return statement('La consigne de température est de {} degrés'.format(str(consigne_temperature)))
    else:
        return statement('La consigne de température est de {} degrés. Mais le chauffage est arrêté'.format(str(consigne_temperature)))

@ask.intent('Consigne_set', mapping={'temperature': 'temperature'})
def consigne_set(temperature):
    consigne_temperature = float(temperature)
    consigne_file = open(CONSIGNE_FILE, "w")
    consigne_file.write(str(consigne_temperature) + '\n')
    consigne_file.close()
    if check_if_alexa_job_exists(chauffage_cron_comment) == True:
        return statement('La consigne de température est de {} degrés'.format(str(consigne_temperature)))
    else:
        return statement('La consigne de température est de {} degrés. Mais le chauffage est arrêté'.format(str(consigne_temperature)))

@ask.intent('Boucle_On')
def boucle_on():
    return gpio_control('actif', "boucle")

@ask.intent('Boucle_Off')
def boucle_off():
    return gpio_control('inactif', "boucle")

@ask.intent('Chaudiere_On')
def chaudiere_on():
    return gpio_control('actif', "chauffe eau")

@ask.intent('Chaudiere_Off')
def chaudiere_off():
    return gpio_control('inactif', "chauffe eau")

@ask.intent('Finish_charge_at', mapping={'percent': 'PERCENT', 'hour': 'HOUR', 'date': 'DATE'})
def finish_charge_at(percent, hour, date):
    cancel_charge()
    current_soc = evnotify_info.get_soc_display()
    try :
        float(current_soc)
    except ValueError:
        return statement("Impossible de récupérer l'état de la la batterie:" + current_soc)
    
    kwh_to_charge = ((float(percent) - current_soc) / 100) * CAR_BATTERY_SIZE_KWH

    if kwh_to_charge <= 0:
        return statement(f"La batterie est déjà au-dessus de {percent}%, pas besoin de charger.")
    
   # Convert end time in datetime format 
    target_datetime = datetime.strptime(f"{date} {hour}", "%Y-%m-%d %H:%M")

    charge_duration_hours = kwh_to_charge / CAR_CHARGING_SPEED_KW
    start_time = target_datetime - timedelta(hours=charge_duration_hours)

    # Comparaison avec maintenant pour savoir si on peut encore programmer la charge
    if start_time > datetime.now():
        
        # Planifier la charge via cron pour démarrer à l'heure calculée
        enable_alexa_job(start_charge_cron_comment, start_charge_cron_command, start_time)

        # Planifier l'arrêt de la charge à l'heure cible
        enable_alexa_job(stop_charge_cron_comment, stop_charge_cron_command, target_datetime)

        # Optimisation du parlé des dates
        readable_start_time = format_date(start_time)
        readable_end_time = format_date(target_datetime)

        return statement(f"Je commencerai la charge {readable_start_time} pour atteindre {percent}% {readable_end_time}.")
        
    else:
        return statement("Il est déjà trop tard pour commencer la charge.")

@ask.intent('SOC_get')
def tell_charge_State():
    soc = evnotify_info.get_soc_display()
    soc_date = evnotify_info.get_last_soc()
    return statement(f"Le pourcentage de charge actuel est de {soc}% lu {format_date(datetime.fromtimestamp(soc_date))} .")

@ask.intent('Cancel_Charge')
def cancel_charge():
    disable_all_alexa_jobs('CRON job powering')
    return statement("Charge abandonnée")

@ask.intent('Daily_charge', mapping={'duration': "DURATION"})
def daily_charge(duration):
    # Annule les autres charges
    cancel_charge() 
    # Convertir la durée en heures et minutes (AMAZON.TIME format)
    charge_duration = datetime.strptime(duration, "%H:%M")
    
    # Définir l'heure de fin à 6h00 et calculer l'heure de début
    end_time = datetime.strptime("06:00", "%H:%M").time()
    start_time = (datetime.combine(datetime.today(), end_time) - timedelta(hours=charge_duration.hour, minutes=charge_duration.minute)).time()

    # Créer les jobs CRON pour allumer et éteindre la prise
    enable_alexa_job(charge_daily_comment, start_charge_cron_command, start_time)
    enable_alexa_job(charge_daily_comment, stop_charge_cron_command, end_time)

    # Confirmer à l'utilisateur
    return statement(f"Je programme une charge quotidienne de {charge_duration.hour} heures et {charge_duration.minute} minutes, débutant à {start_time.strftime('%H:%M')} et se terminant à 6 heures.")



## Delete jobs containing some string
def disable_all_alexa_jobs(cron_title_partial):
    # Parcours de tous les jobs cron
    for job in my_cron:
        # Supprime les jobs ayant un commentaire commençant par "Alexa"
        if cron_title_partial in job.comment:
            my_cron.remove(job)
            my_cron.write()

# Fonction pour convertir l'heure au format "humain" (supprimer le zéro initial)
def format_time(dt):
    hour = int(dt.strftime('%H'))  # On utilise 'int' pour enlever le zéro initial
    minute = int(dt.strftime('%M'))
    if minute !=0:
        return f"{str(hour)} heures {str(minute)}"
    else:
        return f"{str(hour)} heures"

# Permet qu'ALexa utilise les termes aujourd'hui demain et hier au lieu de toujours donner la date entière
def format_date(datetime_not_human):
    # Obtenir la date actuelle
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    # Comparer la date de début de la charge à "demain"
    if datetime_not_human.date() == tomorrow:
        return f"demain à {format_time(datetime_not_human)}"
    elif datetime_not_human.date() == yesterday:
        return f"hier à {format_time(datetime_not_human)}"
    elif datetime_not_human.date() == today:
        return f"aujourd'hui à {format_time(datetime_not_human)}"
    else:
        return f"le {format_time(datetime_not_human)} le {datetime_not_human.strftime('%d %B %Y')}"


if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(debug=True, host="0.0.0.0")
