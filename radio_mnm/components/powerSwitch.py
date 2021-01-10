import time
import logging
logger = logging.getLogger("Radio_mnm")
from handlers import pollingSwitch

import threading

class PowerSwitch():
	"""
	Creates a new switch
	"""
	def __init__(self, radio, gpioPin):
		self.radio = radio
		
		# Create a new switch
		self.powerSwitch = pollingSwitch.Switch(gpioPin)

		self.powerSwitch.addEventListener("on", self.onHandler)
		self.powerSwitch.addEventListener("off", self.offHandler)

	def offHandler(self, event):
		logger.debug("offHandler %r" % event)
		
		self.radio.powerOff()

	def onHandler(self, event):
		logger.debug("onHandler %r" % event)

		self.radio.powerOn()
		