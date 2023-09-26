from flask import Flask
from flask_ask import Ask, statement, convert_errors
import RPi.GPIO as GPIO
import logging, os

GPIO.setmode(GPIO.BCM)

app = Flask(__name__)
ask = Ask(app, '/')
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

@ask.intent('GPIOControlIntent', mapping={'status': 'status', 'pin': 'pin'})
def gpio_control(status, pin):

    try:
        pinNum = int(pin)
    except Exception as e:
        return statement('Pin number not valid.')

    GPIO.setup(pinNum, GPIO.OUT)

    if status in ['on', 'high']:    GPIO.output(pinNum, GPIO.HIGH)
    if status in ['off', 'low']:    GPIO.output(pinNum, GPIO.LOW)

    return statement('Je positionne la pin {} valeur {}'.format(pin, status))

if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(debug=True)