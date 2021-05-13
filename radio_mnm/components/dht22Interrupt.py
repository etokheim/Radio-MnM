import logging
logger = logging.getLogger("Radio_mnm")
import adafruit_dht
from RPi import GPIO
from board import D22
import time
import asyncio

GPIO.setmode(GPIO.BCM)

class Dht22():
	def __init__(self, radio, gpioPin):
		self.gpioPin = gpioPin
		self.radio = radio
		self.sensorDht = adafruit_dht.DHT22(globals()["D" + str(gpioPin)])

		self.radio.offContent = True
		self.temperature = 0.0
		self.humidity = 0.0
		self.lastUpdateTime = int(time.time() * 1000)
		self.update = []
		self.error = []

		self.loop = asyncio.get_event_loop()

		self.loop.create_task(self.tempLoop())

		logger.debug("Listening to DHT22 sensor at GPIO " + str(self.gpioPin))

	async def tempLoop(self):
		while self.loop.is_running():
			await self.getTemp()
			await asyncio.sleep(2)

	async def getTemp(self):
		try:
			temperature = self.sensorDht.temperature
			humidity = self.sensorDht.humidity

			if humidity is not None and temperature is not None:
				# print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))

				# TODO: Getting the temperature and humidity takes freezes the thread for too long – about 300ms
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