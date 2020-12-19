import logging
logger = logging.getLogger("Radio_mnm")
import zope.event.classhandler
import threading
from RPi import GPIO

class off(object):
	def __repr__(self):
		return self.__class__.__name__

class on(object):
	def __repr__(self):
		return self.__class__.__name__

class Switch():
	def __init__(self, gpioPin):
		GPIO.setup(gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		self.gpioPin = gpioPin

		# Add class handlers
		self.on = on
		self.off = off

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
		threading.Timer(.05, lambda: self.handleSwitchChange()).start()

	def handleSwitchChange(self):
		# Switch turned on
		if GPIO.input(self.gpioPin) == 0:
			zope.event.notify(self.on())
			self.state = "on"

		# Switch turned off
		else:
			self.state = "off"
			zope.event.notify(self.off())