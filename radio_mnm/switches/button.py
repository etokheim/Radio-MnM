# A button is a button which has the same state before as after you pushed it.
# A switch on the other hand permanently changes state when pushed. A button
# just temporarily changes state while being pushed.
#
# This means a button can have several events:
# - Down
# - Up
# - Click
# - LongPress
# - VeryLongPress
# - etc.

import logging
logger = logging.getLogger("Radio_mnm")
import gettext
import time
import zope.event.classhandler
import threading

from config import config

_ = config.nno.gettext

if config.raspberry == True:
	from RPi import GPIO
else:
	from EmulatorGUI.EmulatorGUI import GPIO
	
from controls import radio

pushing = False
pushStart = 0
downStart = 0

GPIO.setmode(GPIO.BCM)

# Button 1
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

class click(object):
	def __repr__(self):
		return self.__class__.__name__

class down(object):
	def __repr__(self):
		return self.__class__.__name__

class up(object):
	def __repr__(self):
		return self.__class__.__name__

# Fires when you release the button and you've pushed it longer than the long press threshold
class longClick(object):
	def __repr__(self):
		return self.__class__.__name__

# Fires at once when the long press threshold is reached
class longPress(object):
	def __repr__(self):
		return self.__class__.__name__

# Fires after 5 seconds of pressing
class veryLongPress(object):
	def __repr__(self):
		return self.__class__.__name__


class Button(threading.Thread):
	def __init__(self, gpioPin):
		threading.Thread.__init__(self)
		self.gpioPin = gpioPin

		self.running = True
		# When paused is set, the thread will run, when it's not set, the thread will wait
		self.pauseEvent = threading.Event()

		# Add class handlers
		self.click = click
		self.down = down
		self.up = up
		self.longClick = longClick
		self.longPress = longPress
		self.veryLongPress = veryLongPress

		self.state = "up"

		self.pushing = False
		self.pushStart = 0
		self.downStart = 0
		self.sentLongPressEvent = False
		self.sentVeryLongPressEvent = False

		self.listen = zope.event.classhandler.handler

	# Use Button.start(), not Button.run() to start thread
	# run() would just start a blocking loop
	def run(self):
		while self.running:
			# Wait, if the thread is set on hold
			self.pauseEvent.wait()
			
			time.sleep(0.01)

			button1State = GPIO.input(self.gpioPin)
			holdTime = 0

			if button1State == True and self.pushing == True:
				self.pushing = False

			# If pushing (only executed when state changes)
			if button1State == False and self.pushStart == 0:
				self.pushStart = int(round(time.time() * 1000))
				self.pushing = True
				
				# The holdTime is defined twice because it has to be defined before self.pushStart
				# (as the hold time = now - self.pushStart)
				# TODO: Clean up by defining holdTime once. Just set it to:
				# holdTime = now - self.pushStart == 0 ? now : self.pushStart
				now = int(round(time.time() * 1000))
				holdTime = now - self.pushStart

				zope.event.notify(self.down())
				self.state = "down"

			elif self.pushStart != 0 and self.pushing == False:
				zope.event.notify(self.up())
				self.state = "up"

				if holdTime >= config.longPressThreshold:
					zope.event.notify(self.longClick())
				else:
					if not self.sentLongPressEvent:
						zope.event.notify(self.click())

					# When done pushing, set sentLongPressEvent to False again
					self.sentLongPressEvent = False
					self.sentVeryLongPressEvent = False

				self.pushStart = 0
			
			# If pushing (Executed all the time)
			if button1State == False:
				now = int(round(time.time() * 1000))
				holdTime = now - self.pushStart

			if holdTime >= config.longPressThreshold:
				if self.sentLongPressEvent == False:
					self.sentLongPressEvent = True
					zope.event.notify(self.longPress())

			if holdTime >= config.veryLongPressThreshold:
				if self.sentVeryLongPressEvent == False:
					self.sentVeryLongPressEvent = True
					zope.event.notify(self.veryLongPress())

	def stop(self):
		self.running = False
		logger.warning("Stopped listening to button with GPIO " + str(self.gpioPin))

	def pause(self):
		self.pauseEvent.clear()
		logger.debug("Paused listening to button with GPIO " + str(self.gpioPin))

	def resume(self):
		self.pauseEvent.set()
		logger.debug("Resumed listening to button with GPIO " + str(self.gpioPin))