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
import gettext
import time
import threading
from config.config import config
from RPi import GPIO
from controls import radio

_ = config["getLanguage"].gettext
logger = logging.getLogger("Radio_mnm")

class Button(threading.Thread):
	def __init__(self, gpioPin):
		threading.Thread.__init__(self)
		self.gpioPin = gpioPin

		self.running = True
		# When paused is set, the thread will run, when it's not set, the thread will wait
		self.pauseEvent = threading.Event()

		self.state = "up"

		self.pushing = False
		self.pushStart = 0
		self.downStart = 0
		self.sentLongPressEvent = False
		self.sentVeryLongPressEvent = False

		self.press = []
		self.release = []
		self.click = []
		self.longPress = []
		self.longClick = []
		self.veryLongPress = []

		# Start listening
		self.start()
		self.pauseEvent.set()

		GPIO.setup(gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	# Loops through the callbacks parameter (array) and executes them
	def dispatch(self, callbacks):
		for callback in callbacks:
			if callback:
				callback()

	def addEventListener(self, type, callback):
		if type == "down":
			self.click.append(callback)
		elif type == "press":
			self.press.append(callback)
		elif type == "click":
			self.click.append(callback)
		elif type == "longPress":
			self.longPress.append(callback)
		elif type == "longClick":
			self.longClick.append(callback)
		elif type == "veryLongPress":
			self.veryLongPress.append(callback)

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

				self.dispatch(self.press)
				self.state = "down"

			elif self.pushStart != 0 and self.pushing == False:
				self.dispatch(self.release)
				self.state = "up"

				if holdTime >= config["longPressThreshold"]:
					self.dispatch(self.longClick)
				else:
					if not self.sentLongPressEvent:
						self.dispatch(self.click)

					# When done pushing, set sentLongPressEvent to False again
					self.sentLongPressEvent = False
					self.sentVeryLongPressEvent = False

				self.pushStart = 0
			
			# If pushing (Executed all the time)
			if button1State == False:
				now = int(round(time.time() * 1000))
				holdTime = now - self.pushStart

			if holdTime >= config["longPressThreshold"]:
				if self.sentLongPressEvent == False:
					self.sentLongPressEvent = True
					self.dispatch(self.longPress)

			if holdTime >= config["veryLongPressThreshold"]:
				if self.sentVeryLongPressEvent == False:
					self.sentVeryLongPressEvent = True
					self.dispatch(self.veryLongPress)

		print("Button is running " + str(self.running))

	def stop(self):
		self.running = False
		logger.warning("Stopped listening to button with GPIO " + str(self.gpioPin))

	def pause(self):
		self.pauseEvent.clear()
		logger.debug("Paused listening to button with GPIO " + str(self.gpioPin))

	def resume(self):
		self.pauseEvent.set()
		logger.debug("Resumed listening to button with GPIO " + str(self.gpioPin))
