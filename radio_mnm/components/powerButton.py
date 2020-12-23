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
		self.button.addEventListener("click", self.clickHandler)

	def clickHandler(self):
		logger.debug("powerButtonClickHandler (" + str(self.gpioPin) + ")")
		self.radio.togglePower()