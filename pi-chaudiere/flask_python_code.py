# coding: utf-8

from flask import Flask
from flask_ask import Ask, statement, convert_errors
import RPi.GPIO as GPIO
import logging, os, evnotify_info, datetime
from crontab import CronTab
from urllib.request import urlopen
from datetime import datetime, timedelta

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

CONSIGNE_FILE='/home/pi/repo_chaudiere/pi-chaudiere/CONSIGNE_TEMPERATURE.txt'
READ_TEMP_URL='http://192.168.1.73'

alexa_chauffage_cron_job_comment = 'Alexa CRON job for heater'
alexa_chauffage_cron_job_command = 'python3 /home/pi/repo_chaudiere/pi-chaudiere/2_PLANCHER_AUTO_GPIO16-PIN36.py >> Logs_Chaudiere_2_PLANCHER.log'
alexa_chauffage_cron_job_period = 15

alexa_start_charge_cron_job_comment = 'Alexa CRON job powering ON the plug'
alexa_start_charge_cron_job_command = 'python3 /home/pi/repo_chaudiere/pi-chaudiere/tapo_manager.py turnOn'

alexa_stop_charge_cron_job_comment = 'Alexa CRON job powering OFF the plug'
alexa_stop_charge_cron_job_command = 'python3 /home/pi/repo_chaudiere/pi-chaudiere/tapo_manager.py turnOff'

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

app = Flask(__name__)
ask = Ask(app, '/')
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

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

    returned_statement = returned_statement + ' Le chauffage est ' + boolean2statement[check_if_alexa_job_exists(alexa_chauffage_cron_job_comment)]
    return statement(returned_statement)

@ask.intent('Chauffage_off')
def chauffage_off():
    if check_if_alexa_job_exists(alexa_chauffage_cron_job_comment) == False:
        return statement("Le chauffage était déja éteint")
    else:
        disable_chauffage_alexa_job(alexa_chauffage_cron_job_comment)
        GPIO.output(device2gpio["plancher"], GPIO.LOW)
        return statement('Chauffage éteint')

@ask.intent('Chauffage_on')
def chauffage_on():
    if check_if_alexa_job_exists(alexa_chauffage_cron_job_comment) == True:
        return statement("Le chauffage était déja allumé")
    else:
        enable_periodic_alexa_job(alexa_chauffage_cron_job_comment, alexa_chauffage_cron_job_command, alexa_chauffage_cron_job_period)
        return statement('Chauffage allumé')
    
@ask.intent('Consigne_request')
def consigne_request():
    consigne_file = open(CONSIGNE_FILE, "r")
    consigne_temperature = float(consigne_file.readline())
    consigne_file.close()
    if check_if_alexa_job_exists(alexa_chauffage_cron_job_comment) == True:
        return statement('La consigne de température est de {} degrés'.format(str(consigne_temperature)))
    else:
        return statement('La consigne de température est de {} degrés. Mais le chauffage est arrêté'.format(str(consigne_temperature)))

@ask.intent('Consigne_set', mapping={'temperature': 'temperature'})
def consigne_set(temperature):
    consigne_temperature = float(temperature)
    consigne_file = open(CONSIGNE_FILE, "w")
    consigne_file.write(str(consigne_temperature) + '\n')
    consigne_file.close()
    if check_if_alexa_job_exists(alexa_chauffage_cron_job_comment) == True:
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

        # Obtenir la date actuelle
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        disable_all_alexa_jobs('CRON job powering')
        # Planifier la charge via cron pour démarrer à l'heure calculée
        enable_alexa_job(alexa_start_charge_cron_job_comment, alexa_start_charge_cron_job_command, start_time)

        # Planifier l'arrêt de la charge à l'heure cible
        enable_alexa_job(alexa_stop_charge_cron_job_comment, alexa_stop_charge_cron_job_command, target_datetime)


        # Comparer la date de début de la charge à "demain"
        if start_time.date() == tomorrow:
            readable_start_time = f"demain à {format_time(start_time)}"
        else:
            readable_start_time = f"{format_time(start_time)} le {start_time.strftime('%d %B %Y')}"

        # Comparer la date de fin de la charge à "demain"
        if target_datetime.date() == tomorrow:
            readable_end_time = f"demain à {format_time(target_datetime)}"
        else:
            readable_end_time = f"{format_time(target_datetime)} le {target_datetime.strftime('%d %B %Y')}"
        
        return statement(f"Je commencerai la charge {readable_start_time} pour atteindre {percent}% {readable_end_time}.")
        
    else:
        return statement("Il est déjà trop tard pour commencer la charge.")

@ask.intent('SOC_get')
def tell_charge_State():
    soc = evnotify_info.get_soc_display()
    soc_date = evnotify_info.get_last_soc_readable()
    return statement(f"Le pourcentage de charge actuel est de {soc}% lu à {soc_date} .")

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
    minute = dt.strftime('%M')
    return f"{hour} heures {minute}"

if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(debug=True, host="0.0.0.0")
