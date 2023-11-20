# coding: utf-8

from flask import Flask
from flask_ask import Ask, statement, convert_errors
import RPi.GPIO as GPIO
import logging, os
from crontab import CronTab
from urllib.request import urlopen

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

CONSIGNE_FILE='/home/pi/repo_chaudiere/pi-chaudiere/CONSIGNE_TEMPERATURE.txt'
READ_TEMP_URL='http://192.168.1.73'

alexa_chauffage_cron_job_comment = 'Alexa_cron_job_comment'
alexa_chauffage_cron_job_command = 'python3 /home/pi/repo_chaudiere/pi-chaudiere/2_PLANCHER_AUTO_GPIO20-PIN38.py >> Logs_Chaudiere_2_PLANCHER.log'
alexa_chauffage_cron_job_period = 15

my_cron = CronTab(user='pi')

boolean2statement = dict()
boolean2statement[0] = 'éteint'
boolean2statement[1] = 'allumé'

device2gpio=dict()
device2gpio["chaudière"]=21
device2gpio["chauffe eau"]=21
device2gpio["eau chaude"]=21

device2gpio["boucle"]=16
device2gpio["e. c. s. "]=16

device2gpio["plancher"]=20
device2gpio["chauffage"]=20

# set all gpio as output
for device in device2gpio:
    GPIO.setup(device2gpio[device], GPIO.OUT)

def check_if_alexa_job_exists():
    for job in my_cron:
        if job.comment == alexa_chauffage_cron_job_comment:
            return True
    return False

def disable_chauffage_alexa_job():
    for job in my_cron:
        if job.comment == alexa_chauffage_cron_job_comment:
            my_cron.remove(job)
            my_cron.write()

def enable_chauffage_alexa_job():
    job = my_cron.new(command=alexa_chauffage_cron_job_command, comment=alexa_chauffage_cron_job_comment)
    job.minute.every(alexa_chauffage_cron_job_period)
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

    returned_statement = returned_statement + ' Le chauffage est ' + boolean2statement[check_if_alexa_job_exists()]
    return statement(returned_statement)

@ask.intent('Chauffage_off')
def chauffage_off():
    if check_if_alexa_job_exists() == False:
        return statement("Le chauffage était déja éteint")
    else:
        disable_chauffage_alexa_job()
        GPIO.output(device2gpio["plancher"], GPIO.LOW)
        return statement('Chauffage éteint')

@ask.intent('Chauffage_on')
def chauffage_on():
    if check_if_alexa_job_exists() == True:
        return statement("Le chauffage était déja allumé")
    else:
        enable_chauffage_alexa_job()
        return statement('Chauffage allumé')
    
@ask.intent('Consigne_request')
def consigne_request():
    consigne_file = open(CONSIGNE_FILE, "r")
    consigne_temperature = float(consigne_file.readline())
    consigne_file.close()
    if check_if_alexa_job_exists() == True:
        return statement('La consigne de température est de {} degrés'.format(str(consigne_temperature)))
    else:
        return statement('La consigne de température est de {} degrés. Mais le chauffage est arrêté'.format(str(consigne_temperature)))

@ask.intent('Consigne_set', mapping={'temperature': 'temperature'})
def consigne_set(temperature):
    consigne_temperature = float(temperature)
    consigne_file = open(CONSIGNE_FILE, "w")
    consigne_file.write(str(consigne_temperature) + '\n')
    consigne_file.close()
    if check_if_alexa_job_exists() == True:
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
def boucle_off():
    return gpio_control('inactif', "chauffe eau")


if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(debug=True, host="0.0.0.0")
