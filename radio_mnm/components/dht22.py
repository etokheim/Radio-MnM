import logging
logger = logging.getLogger("Radio_mnm")
import adafruit_dht
from RPi import GPIO
from board import D22
import time
import threading

GPIO.setmode(GPIO.BCM)

class Dht22(threading.Thread):
	def __init__(self, radio, gpioPin):
		threading.Thread.__init__(self)
		self.gpioPin = gpioPin
		self.radio = radio
		self.sensorDht = adafruit_dht.DHT22(globals()["D" + str(gpioPin)])

		self.running = True
		self.start()
		self.radio.offContent = True
		self.temperature = 0.0
		self.humidity = 0.0
		self.lastUpdateTime = int(time.time() * 1000)
		self.update = []
		self.error = []

	def run(self):
		logger.debug("Listening to DHT22 sensor at GPIO " + str(self.gpioPin))

		while self.running:
			try:
				temperature = self.sensorDht.temperature
				humidity = self.sensorDht.humidity

				if humidity is not None and temperature is not None:
					# print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))
					self.temperature = temperature
					self.humidity = humidity
					self.lastUpdateTime = int(time.time() * 1000)
					
					self.dispatch(self.update, {
						"temperature": temperature,
						"humidity": humidity,
						"timestamp": self.lastUpdateTime
					})
				else:
					print("Failed to retrieve data from humidity sensor")

				if int(time.time() * 1000) - self.lastUpdateTime > 60000:
					self.dispatch(self.error, {
						"error": 500,
						"message": "Sensor stopped sending data. Temperature and humidity is outdated."
					})

				time.sleep(2)
			except RuntimeError as exception:
				logger.warning("Failed to get data from sensor on GPIO " + str(self.gpioPin) + ":")
				logger.warning(exception)

	def stop(self):
		self.running = False
		logger.warning("Stopped listening to the DHT22 sensor at GPIO " + str(self.gpioPin))

	# Loops through the callbacks parameter (array) and executes them
	def dispatch(self, callbacks, event):
		for callback in callbacks:
			if callback:
				callback(event)

	def addEventListener(self, type, callback):
		if type == "update":
			self.update.append(callback)
		elif type == "error":
			self.error.append(callback)
		else:
			raise Exception("Event type " + str(callback) + "is not supported.")