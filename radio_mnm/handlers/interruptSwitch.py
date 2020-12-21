import logging
logger = logging.getLogger("Radio_mnm")
import zope.event.classhandler
import threading
from RPi import GPIO

class Switch():
	def __init__(self, gpioPin):
		self.lastGpioState = 0
		GPIO.setup(gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		self.lastExecution = 0
		self.gpioPin = gpioPin

		# Add listen handler
		self.listen = zope.event.classhandler.handler

		# State (string)
		# "on" || "off"
		self.state = "off"

		# Listen to events
		logger.debug("Listening to switch (GPIO " + str(self.gpioPin) + ")")
		GPIO.add_event_detect(gpioPin, GPIO.BOTH, callback=self.delayHandling, bouncetime=50)

		# Run the switch handler once, as the first state won't trigger an interrupt event
		self.delayHandling(self.gpioPin)

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
			zope.event.notify(self.on())
			print(self.state)

		# Switch turned off
		elif gpioState == 1 and self.state != "off":
			self.state = "off"
			zope.event.notify(self.off())
			print(self.state)

		else:
			logger.warning("Switch from and to same state...")

	class off(object):
		def __repr__(self):
			return self.__class__.__name__

	class on(object):
		def __repr__(self):
			return self.__class__.__name__