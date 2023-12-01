import RPi.GPIO as GPIO
from datetime import datetime

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(36,GPIO.OUT)

GPIO.output(36,GPIO.HIGH)
current_date=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#Log Format: Timestamp;Action;GPIO16_STATE;PIN36_STATE;LED_STATE
print(current_date + ";Allumage_Plancher;GPIO16=1;PIN36=1;OFF")
