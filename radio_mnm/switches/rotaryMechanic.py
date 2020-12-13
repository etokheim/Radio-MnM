# 
#
# A rotary decoder can have several events:
# - Rotate right
# - Rotate left
# - Click
# - LongPress
# - VeryLongPress

import logging
logger = logging.getLogger("Radio_mnm")
import gettext
import time
import zope.event
import zope.event.classhandler
import threading

from config import config

_ = config.nno.gettext

if config.raspberry == True:
	from RPi import GPIO
else:
	from EmulatorGUI.EmulatorGUI import GPIO
	
from controls import radio

GPIO.setmode(GPIO.BCM)

class click(object):
	def __repr__(self):
		return self.__class__.__name__

class left(object):
	def __repr__(self):
		return self.__class__.__name__

class right(object):
	def __repr__(self):
		return self.__class__.__name__

class press(object):
	def __repr__(self):
		return self.__class__.__name__

class release(object):
	def __repr__(self):
		return self.__class__.__name__

# Fires when you release the button and you've pushed it longer than the long press threshold
class longPress(object):
	def __repr__(self):
		return self.__class__.__name__

# Fires at once when the long press threshold is reached
class longRelease(object):
	def __repr__(self):
		return self.__class__.__name__

# Fires after 5 seconds of pressing
class veryLongPress(object):
	def __repr__(self):
		return self.__class__.__name__


class Rotary(threading.Thread):
	def __init__(self, clk, dt, switch):
		threading.Thread.__init__(self)
		
		self.clk = clk
		self.dt = dt
		self.switch = switch

		self.running = True
		# When paused is set, the thread will run, when it's not set, the thread will wait
		self.pauseEvent = threading.Event()

		# Add class handlers
		self.click = click
		self.left = left
		self.right = right
		self.press = press
		self.release = release

		self.listen = zope.event.classhandler.handler

		# Set up GPIO pins
		GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		if switch != False:
			GPIO.setup(switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		else:
			logger.debug("The rotary encoder wasn't setup with a switch")

		# Listen for events on the CLK pin
		GPIO.add_event_detect(clk, GPIO.FALLING, callback=self.rotationHandler, bouncetime=50)
		GPIO.add_event_detect(switch, GPIO.BOTH, callback=self.switchHandler, bouncetime=50)

	def rotationHandler(self, channel):
		if GPIO.input(self.dt) == 1:
			zope.event.notify(self.right())
			logger.debug("Rotary right")
		else:
			zope.event.notify(self.left())
			logger.debug("Rotary left")

	def switchHandler(self, channel):
		if GPIO.input(self.switch) == 0:
			zope.event.notify(self.press())
			logger.debug("Rotary button press event")
		else:
			zope.event.notify(self.release())
			logger.debug("Rotary button release event")
