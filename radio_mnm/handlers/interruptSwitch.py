import logging
logger = logging.getLogger("Radio_mnm")
import threading
from RPi import GPIO

GPIO.setmode(GPIO.BCM)

class Switch():
	def __init__(self, gpioPin):
		self.lastGpioState = 0
		GPIO.setup(gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		self.lastExecution = 0
		self.gpioPin = gpioPin

		self.on = []
		self.off = []

		# State (string)
		# "on" || "off"
		self.state = "off"

		# Listen to events
		logger.debug("Listening to switch (GPIO " + str(self.gpioPin) + ")")
		GPIO.add_event_detect(gpioPin, GPIO.BOTH, callback=self.delayHandling, bouncetime=50)

		# Run the switch handler once, as the first state won't trigger an interrupt event
		self.delayHandling(self.gpioPin)

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

	# Delays the handling of the button state a little so we don't get the wrong reading
	# due to the noise
	def delayHandling(self, channel):
		lastGpioState = self.lastGpioState
		gpioState = GPIO.input(self.gpioPin)
		print(str(lastGpioState) + ", " + str(gpioState))

		self.lastGpioState = gpioState
		# threading.Timer(.1, lambda: self.handleSwitchChange()).start()

	def handleSwitchChange(self):
		gpioState = GPIO.input(self.gpioPin)

		# Switch turned on
		if gpioState == 0 and self.state != "on":
			self.state = "on"
			self.dispatch(self.on)
			print(self.state)

		# Switch turned off
		elif gpioState == 1 and self.state != "off":
			self.state = "off"
			self.dispatch(self.off)
			print(self.state)

		else:
			logger.warning("Switch from and to same state...")