import logging
logger = logging.getLogger("Radio_mnm")
import time
import zope.event.classhandler
from threading import Thread
from RPi import GPIO
from controls import radio

GPIO.setmode(GPIO.BCM)

class Switch(Thread):
	def __init__(self, gpioPin):
		Thread.__init__(self)
		self.running = True
		self.gpioPin = gpioPin

		self.pushing = False

		self.listen = zope.event.classhandler.handler

		GPIO.setup(self.gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		self.start()

	# Use Switch.start(), not Switch.run() to start thread
	# run() would just start a blocking loop
	def run(self):
		logger.debug("Listening on power button (GPIO " + str(self.gpioPin) + ")")

		while self.running:
			time.sleep(0.25)
		
			button2State = GPIO.input(self.gpioPin)

			# If pushing
			if button2State == False:
				# Only send wake event if state changed
				if self.pushing == False:
					# Send wake event
					zope.event.notify(self.on())

				self.pushing = True

			else:
				if self.pushing == True:
					# Send sleep event
					zope.event.notify(self.off())

					self.pushing = False

	def stop(self):
		self.running = False
		logger.warning("Stopped listening to the power switch")

	class off(object):
		def __repr__(self):
			return self.__class__.__name__

	class on(object):
		def __repr__(self):
			return self.__class__.__name__