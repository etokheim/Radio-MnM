import logging
logger = logging.getLogger("Radio_mnm")
import time
from threading import Thread
from RPi import GPIO
from controls import radio

GPIO.setmode(GPIO.BCM)

class Switch(Thread):
	def __init__(self, gpioPin):
		Thread.__init__(self)
		self.running = True
		self.gpioPin = gpioPin

		self.pushing = False

		self.on = []
		self.off = []

		GPIO.setup(self.gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		self.start()

	# Loops through the callbacks parameter (array) and executes them
	def dispatch(self, callbacks):
		for callback in callbacks:
			if callback:
				callback()

	def addEventListener(self, type, callback):
		if type == "on":
			self.on.append(callback)
		elif type == "off":
			self.off.append(callback)
		else:
			raise Exception("Event type " + str(callback) + "is not supported.")

	# Use Switch.start(), not Switch.run() to start thread
	# run() would just start a blocking loop
	def run(self):
		logger.debug("Listening on power button (GPIO " + str(self.gpioPin) + ")")

		while self.running:
			time.sleep(0.25)
		
			button2State = GPIO.input(self.gpioPin)

			# If pushing
			if button2State == False:
				# Only send wake event if state changed
				if self.pushing == False:
					# Send wake event
					self.dispatch(self.on)

				self.pushing = True

			else:
				if self.pushing == True:
					# Send sleep event
					self.dispatch(self.off)

					self.pushing = False

	def stop(self):
		self.running = False
		logger.warning("Stopped listening to the power switch")

	class off(object):
		def __repr__(self):
			return self.__class__.__name__

	class on(object):
		def __repr__(self):
			return self.__class__.__name__