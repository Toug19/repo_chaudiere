import RPi.GPIO as GPIO
from datetime import datetime

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(38,GPIO.OUT)

GPIO.output(38,GPIO.HIGH)
current_date=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#Log Format: Timestamp;Action;GPIO16_STATE;PIN36_STATE;LED_STATE
print(current_date + ";Allumage ECS;GPIO20=1;PIN38=1;OFF")
