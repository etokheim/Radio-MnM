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
		self.longPress = longPress
		self.longRelease = longRelease
		self.veryLongPress = veryLongPress

		self.state = "up"

		self.pushStart = False
		self.sentLongPressEvent = False
		self.sentVeryLongPressEvent = False

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
		# print("GPIO", channel, "triggered. States: 16 =", str(GPIO.input(16)), "20 =", str(GPIO.input(20)))

		if GPIO.input(self.dt) == 1:
			print("Right")
			zope.event.notify(self.right())
		else:
			print("Left")
			zope.event.notify(self.left())

	def switchHandler(self, channel):
		if GPIO.input(self.switch) == 0:
			print("Button was pressed")
		else:
			print("Button was released")

	# Use Button.start(), not Button.run() to start thread
	# run() would just start a blocking loop
	# def run(self):
	# 	while self.running:
	# 		# Wait, if the thread is set on hold
	# 		self.pauseEvent.wait()
			
	# 		time.sleep(0.01)

	# 		button1State = GPIO.input(self.gpioPin)
	# 		holdTime = 0

	# 		if button1State == True and self.pushing == True:
	# 			self.pushing = False

	# 		# If pushing (only executed when state changes)
	# 		if button1State == False and self.pushStart == 0:
	# 			self.pushStart = int(round(time.time() * 1000))
	# 			self.pushing = True
				
	# 			# The holdTime is defined twice because it has to be defined before self.pushStart
	# 			# (as the hold time = now - self.pushStart)
	# 			# TODO: Clean up by defining holdTime once. Just set it to:
	# 			# holdTime = now - self.pushStart == 0 ? now : self.pushStart
	# 			now = int(round(time.time() * 1000))
	# 			holdTime = now - self.pushStart

	# 			zope.event.notify(self.down())
	# 			self.state = "down"

	# 		elif self.pushStart != 0 and self.pushing == False:
	# 			zope.event.notify(self.up())
	# 			self.state = "up"

	# 			if holdTime >= config.longPressThreshold:
	# 				zope.event.notify(self.longClick())
	# 			else:
	# 				if not self.sentLongPressEvent:
	# 					zope.event.notify(self.click())

	# 				# When done pushing, set sentLongPressEvent to False again
	# 				self.sentLongPressEvent = False
	# 				self.sentVeryLongPressEvent = False

	# 			self.pushStart = 0
			
	# 		# If pushing (Executed all the time)
	# 		if button1State == False:
	# 			now = int(round(time.time() * 1000))
	# 			holdTime = now - self.pushStart

	# 		if holdTime >= config.longPressThreshold:
	# 			if self.sentLongPressEvent == False:
	# 				self.sentLongPressEvent = True
	# 				zope.event.notify(self.longPress())

	# 		if holdTime >= config.veryLongPressThreshold:
	# 			if self.sentVeryLongPressEvent == False:
	# 				self.sentVeryLongPressEvent = True
	# 				zope.event.notify(self.veryLongPress())

	# def stop(self):
	# 	self.running = False
	# 	logger.warning("Stopped listening to button with GPIO " + str(self.gpioPin))

	# def pause(self):
	# 	self.pauseEvent.clear()
	# 	logger.debug("Paused listening to button with GPIO " + str(self.gpioPin))

	# def resume(self):
	# 	self.pauseEvent.set()
	# 	logger.debug("Resumed listening to button with GPIO " + str(self.gpioPin))