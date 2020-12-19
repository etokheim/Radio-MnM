import logging
logger = logging.getLogger("Radio_mnm")
from config import config
import time
import zope.event.classhandler
from threading import Thread
import gettext

_ = config.nno.gettext

if config.raspberry == True:
	from RPi import GPIO
else:
	from EmulatorGUI.EmulatorGUI import GPIO

from controls import radio
from config import config

class up(object):
	def __repr__(self):
		return self.__class__.__name__

class down(object):
	def __repr__(self):
		return self.__class__.__name__

class Switch(Thread):
	def __init__(self, gpioPin):
		Thread.__init__(self)
		GPIO.setup(gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		self.running = True
		self.gpioPin = gpioPin

		# Add class handlers
		self.down = down
		self.up = up

		self.pushing = False

		self.listen = zope.event.classhandler.handler

	# Use Switch.start(), not Switch.run() to start thread
	# run() would just start a blocking loop
	def run(self):
		logger.debug("Listening to switch (GPIO " + str(self.gpioPin) + ")")

		while self.running:
			time.sleep(config.checkPowerSwitchStateInterval)
		
			button2State = GPIO.input(self.gpioPin)

			# If pushing
			if button2State == False:
				# Only send wake event if state changed
				if self.pushing == False:
					# Send wake event
					zope.event.notify(self.down())

				self.pushing = True

			else:
				if self.pushing == True:
					# Send sleep event
					zope.event.notify(self.up())

					self.pushing = False

	def stop(self):
		self.running = False
		logger.warning("Stopped listening GPIO " + str(self.gpioPin) + " switch")