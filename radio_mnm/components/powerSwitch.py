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

		self.powerSwitch.listen(self.powerSwitch.on, self.onHandler)
		self.powerSwitch.listen(self.powerSwitch.off, self.offHandler)

	def offHandler(self, event):
		logger.debug("offHandler %r" % event)
		
		# TODO: Most of this should go into a self.radio.off() method.
		self.radio.on = False
		self.radio.stop()
		self.radio.display.pause()
		# Find a way to implement this into the buttons, if it helps with the standby mode compute.
		# button.pause()
		self.radio.handleSendState("suspended")

		# I'm not quite sure I have to reset all of these values
		self.radio.display.currentlyDisplayingMessage = ""
		self.radio.display.notificationMessage = ""
		self.radio.display.lastDisplayedMessage = ""
		self.radio.display.lastDisplayedCroppedMessage = ""

	def onHandler(self, event):
		logger.debug("onHandler %r" % event)

		# TODO: Most of this should go into a self.radio.on() method.
		self.radio.on = True
		self.radio.display.resume()
		# Find a way to implement this into the buttons, if it helps with the standby mode compute.
		# button.resume()

		self.radio.turnOnTime = int(round(time.time() * 1000))

		if not self.radio.selectedChannel:
			self.radio.selectedChannel = self.radio.channels[0]
		
		# Start playing
		self.radio.play()

		# TODO: Maybe rename .start() methods that aren't threads, as it can be confusing.
		# Starts the registration if the radio isn't registered
		self.radio.registration.start()

		if self.radio.lastPowerState != "off":
			self.radio.handleSendState("noPower")

		self.radio.handleSendState("on")

		# if len(self.radio.channels) > 0:
		# 	self.radio.play()
