import logging
logger = logging.getLogger("Radio_mnm")
import adafruit_dht
from RPi import GPIO
# from board import D22
import time
import threading

class TemperatureAndHumidity(threading.Thread):
	def __init__(self, radio, gpioPin):
		threading.Thread.__init__(self)
		self.gpioPin = gpioPin
		GPIO.setup(gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		# sensorDht = adafruit_dht.DHT22(D22)
		self.sensorDht = adafruit_dht.DHT22(GPIO.input(gpioPin))

		self.running = True
		self.start()
		self.radio.offContent = True

	def run(self):
		logger.debug("Listening to DHT22 sensor at GPIO " + str(self.gpioPin))

		while self.running:
			temperature = self.sensorDht.temperature
			humidity = self.sensorDht.humidity

			if humidity is not None and temperature is not None:
				print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))
			else:
				print("Failed to retrieve data from humidity sensor")

			time.sleep(1)

	def stop(self):
		self.running = False
		logger.warning("Stopped listening to the DHT22 sensor at GPIO " + str(self.gpioPin))
