# coding: utf-8

from flask import Flask
from flask_ask import Ask, statement, convert_errors
import RPi.GPIO as GPIO
import logging, os

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

boolean2statement = dict()
boolean2statement[0] = 'inactif'
boolean2statement[1] = 'actif'

device2gpio=dict()
device2gpio["chauffe eau"]=21
device2gpio["eau chaude"]=21

device2gpio["boucle"]=16
device2gpio["e. c. s. "]=16

# set all gpio as output
for device in device2gpio:
    GPIO.setup(device2gpio[device], GPIO.OUT)


app = Flask(__name__)
ask = Ask(app, '/')
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

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

    return statement('Je positionne {} à la valeur {}'.format(device, status))

@ask.intent('GPIOStatusIntent')
def gpio_status():
    returned_statement = str()
    previous_device_pin = 0

    for device in device2gpio:
        if previous_device_pin != device2gpio[device]:
            returned_statement = returned_statement + ' ' + device + ' ' + 'est à ' + boolean2statement[GPIO.input(device2gpio[device])] + '.'
        previous_device_pin = device2gpio[device]
        
    return statement(returned_statement)


if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(debug=True, host="0.0.0.0")
