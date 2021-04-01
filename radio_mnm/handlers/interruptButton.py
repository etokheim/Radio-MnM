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
from config.config import config
from RPi import GPIO
from controls import radio
import asyncio

GPIO.setmode(GPIO.BCM)

_ = config["getLanguage"].gettext
logger = logging.getLogger("Radio_mnm")

class Button():
	def __init__(self, gpioPin):
		self.gpioPin = gpioPin
		self.loop = asyncio.get_event_loop()

		self.state = "released"

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

		GPIO.setup(gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(gpioPin, GPIO.BOTH, callback=self.handleInterrupt, bouncetime=50)

	# Loops through the callbacks parameter (array) and executes them
	async def dispatch(self, callbacks):
		for callback in callbacks:
			if callback:
				callback()

	def addEventListener(self, type, callback):
		if type == "press":
			self.press.append(callback)
		elif type == "release":
			self.release.append(callback)
		elif type == "click":
			self.click.append(callback)
		elif type == "longPress":
			self.longPress.append(callback)
		elif type == "longClick":
			self.longClick.append(callback)
		elif type == "veryLongPress":
			self.veryLongPress.append(callback)
		else:
			raise Exception("Event type " + str(callback) + "is not supported.")

	def handleInterrupt(self, channel):
		# If the button is pressed
		if not GPIO.input(self.gpioPin) and not self.pushing:
			self.pushStart = int(round(time.time() * 1000))
			self.loop.create_task(self.dispatch(self.press))
			self.pushing = True
			logger.debug("Button press (GPIO " + str(self.gpioPin) + ")")

		# The button is released
		elif self.pushing:
			self.loop.create_task(self.dispatch(self.release))
			holdTime = int(round(time.time() * 1000)) - self.pushStart
			logger.debug("Button release (GPIO " + str(self.gpioPin) + ")")
			self.pushing = False

			if holdTime > config["longPressThreshold"]:
				logger.debug("Button longClick (GPIO " + str(self.gpioPin) + ")")
				self.loop.create_task(self.dispatch(self.longClick))

			# TODO: Add support for long press event (which fires while holding the button)
