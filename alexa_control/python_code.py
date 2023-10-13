# coding: utf-8

from flask import Flask
from flask_ask import Ask, statement, convert_errors
import RPi.GPIO as GPIO
import logging, os

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
device2gpio=dict()
device2gpio["chauffe eau"]=21
device2gpio["eau chaude"]=21

device2gpio["boucle"]=16
device2gpio["e. c. s. "]=16


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

    GPIO.setup(pinNum, GPIO.OUT)

    if status in ['on', 'actif']:    GPIO.output(pinNum, GPIO.HIGH)
    if status in ['off', 'inactif']:    GPIO.output(pinNum, GPIO.LOW)

    return statement('Je positionne {} à la valeur {}'.format(device, status))

if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(debug=True, host="0.0.0.0")
