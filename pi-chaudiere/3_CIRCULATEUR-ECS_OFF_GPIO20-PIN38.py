import RPi.GPIO as GPIO
from datetime import datetime

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(38,GPIO.OUT)

GPIO.output(38,GPIO.LOW)
current_date=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#Log Format: Timestamp;Action;GPIO20_STATE;PIN38_STATE;LED_STATE
print(current_date + ";Extinction ECS;GPIO20=0;PIN38=0;ON")
