import os
import time
import handlers.button
import threading
from config.config import config
import logging
logger = logging.getLogger("Radio_mnm")

_ = config["getLanguage"].gettext

class PowerButton():
	def __init__(self, radio, gpioPin):
		self.radio = radio
		self.gpioPin = gpioPin
		self.downStart = None

		self.button = handlers.button.Button(gpioPin)

		self.button.listen(self.button.click, self.buttonClickHandler)
		self.button.listen(self.button.down, self.buttonDownHandler)
		self.button.listen(self.button.up, self.buttonUpHandler)
		self.button.listen(self.button.longPress, self.buttonLongPressHandler)
		self.button.listen(self.button.veryLongPress, self.buttonVeryLongPressHandler)

	# Event is set to the the event which calls it. In this function's case it should be
	# set to "click".
	def buttonClickHandler(self, event):
		logger.debug("powerButtonClickHandler (" + str(self.gpioPin) + ") %r" % event)
		self.radio.togglePower()

	def buttonDownHandler(self, event):
		logger.debug("powerButtonDownHandler (" + str(self.gpioPin) + ") %r" % event)
		self.downStart = int(round(time.time() * 1000))

	def buttonUpHandler(self, event):
		logger.debug("powerButtonUpHandler (" + str(self.gpioPin) + ") %r" % event)
		self.downStart = 0

	def buttonLongPressHandler(self, event):
		logger.debug("powerButtonLongPressHandler (" + str(self.gpioPin) + ") %r" % event)
		
	def buttonVeryLongPressHandler(self, event):
		logger.debug("powerButtonVeryLongPressHandler (" + str(self.gpioPin) + ") %r" % event)