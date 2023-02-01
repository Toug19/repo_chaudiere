import os
import glob
from datetime import datetime

GENERAL_SENSOR_PATH='/sys/bus/w1/devices/10*/temperature'

def find_sensors_paths(general_sensor_path):
	"""return a list containing with the files with the temperature for each sensor"""
	return glob.glob(GENERAL_SENSOR_PATH)

def read_sensors_temperatures(paths_list):
	temperatures_dict=dict()
	for path in paths_list:
		with open(path) as temperature_file:
			temperature = temperature_file.read()
		temperatures_dict[path]=temperature[:-1]
	return temperatures_dict

def calculate_mean_temperature(temperatures_dict):
	value_number=int(0)
	temperature_int=int(0)
	for temperature in temperatures_dict.values():
		try:
			temperature_int=temperature_int+int(temperature)
			value_number+=1
		except:
			print("Exception occured")

	return(temperature_int/value_number)

def write_temperature_in_index(temperature,path):
	with open(path,'w') as webpage:
		webpage.write(str(temperature))



if __name__ == '__main__':
	sensor_path_list=find_sensors_paths(GENERAL_SENSOR_PATH)

	temperatures_dict=read_sensors_temperatures(sensor_path_list)

	current_date=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
	value_number=0
	temperature_int=0
	for sensor in temperatures_dict.keys():
		try:
			temperature_read = temperatures_dict[sensor]
			if temperature_read != '85000':
				temperature_int=temperature_int+int(temperature_read)
				value_number+=1
				print(current_date + ";"+ sensor + ";" + temperature_read)
			else:
				print(current_date + ";"+ sensor + ";" + temperature_read + ";WRONG TEMPERATURE")
		except:
			print(current_date + ";"+ sensor + "; EXCEPTION OCCURRED")
	temperature_mean = temperature_int / value_number
	print(current_date + ";MEAN_TEMP;" + str(temperature_mean))

	write_temperature_in_index(temperature_mean/1000, '/var/www/html/index.html')



