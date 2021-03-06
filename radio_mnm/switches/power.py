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

# Button 2
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# I really have no idea how Zope events works, but this project is a very "learn
# as we go" project. Anyways, what I wanted to do here was to create an event system
# where I could subscribe to several events: click, down, up, longClick. This I
# figured out, but I'm still unable to pass arguments down to the event handlers.
# But as I don't need to pass down arguments yet, It's not a big problem yet. An
# example of arguments could be an event for clicking the mouse. That should resolve
# in an event, click, with arguments like pointer position x and y.

class up(object):
	def __repr__(self):
		return self.__class__.__name__

class down(object):
	def __repr__(self):
		return self.__class__.__name__

class Switch(Thread):
	def __init__(self, gpioPin):
		Thread.__init__(self)
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
		logger.debug("Listening on power button (GPIO " + str(self.gpioPin) + ")")

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
		logger.warning("Stopped listening to the power switch")