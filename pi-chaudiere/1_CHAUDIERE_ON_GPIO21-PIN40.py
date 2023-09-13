import RPi.GPIO as GPIO
from datetime import datetime

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(40,GPIO.OUT)

GPIO.output(40,GPIO.HIGH)
current_date=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#Log Format: Timestamp;Action;GPIO21_STATE;PIN40_STATE;LED1_STATE
print(current_date + ";Allumage_chaudiere;1;1;OFF")
