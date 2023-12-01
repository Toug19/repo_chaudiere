import RPi.GPIO as GPIO
from urllib.request import urlopen
from re import findall, compile
from datetime import datetime
from urllib.request import urlopen


URL='http://192.168.1.73'
CONSIGNE_FILE='/home/pi/repo_chaudiere/pi-chaudiere/CONSIGNE_TEMPERATURE.txt'
url = "https://www.infoclimat.fr/observations-meteo/temps-reel/toulouse-blagnac/07630.html?"
per_hour_temperature_regex = 'Minimale sur 1h : (-*\d*.\d)&deg'
per_hour_temperature_compiled_regex = compile(per_hour_temperature_regex)



def read_temperature_on_webpage(url):
	return float(urlopen(url).read().decode('utf8'))

def read_consigne_temperature(file_path):
	with open(file_path,'r') as consigne_file:
		consigne=consigne_file.readline()
	return float(consigne)


if __name__ == '__main__':

	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(36,GPIO.OUT)

	#GPIO.output(36,GPIO.HIGH)
	current_date=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
	#print(current_date + ";Allumage Plancher;GPIO16=1;PIN36=1")
	current_temperature = read_temperature_on_webpage(URL)
	consigne_temperature = read_consigne_temperature(CONSIGNE_FILE)

	#page = urlopen(url)
	#html_bytes = page.read()
	#html = html_bytes.decode("utf-8")

	#web_page_temperatures = findall(per_hour_temperature_compiled_regex, html)


	# Log format: Timestamp;Action;GPIO16_STATE;PIN36_STATE;LED2_STATE;CONSIGNE_TEMPERATURE;READ_TEMPERATURE;1h_min_ext_temperature
	if current_temperature > consigne_temperature:
		GPIO.output(36,GPIO.LOW)
		#print(current_date + ";Plancher_OFF;0;0;ON;" + str(consigne_temperature) + ";" + str(current_temperature) + ";" + str(web_page_temperatures[0]))
		print(current_date + ";Plancher_OFF;0;0;ON;" + str(consigne_temperature) + ";" + str(current_temperature))
	else:
		GPIO.output(36,GPIO.HIGH)
		#print(current_date + ";Plancher_ON;1;1;OFF;" + str(consigne_temperature) + ";" + str(current_temperature) + ";" + str(web_page_temperatures[0]))
		print(current_date + ";Plancher_ON;1;1;OFF;" + str(consigne_temperature) + ";" + str(current_temperature))
