import logging
logger = logging.getLogger("Radio_mnm")
import zope.event
import zope.event.classhandler
import threading
from RPi import GPIO
	
class Rotary(threading.Thread):
	def __init__(self, clk, dt):
		threading.Thread.__init__(self)
		
		self.clk = clk
		self.dt = dt

		self.running = True
		# When paused is set, the thread will run, when it's not set, the thread will wait
		self.pauseEvent = threading.Event()

		self.listen = zope.event.classhandler.handler

		# Set up GPIO pins
		GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		# Listen for events on the CLK pin
		GPIO.add_event_detect(clk, GPIO.FALLING, callback=self.rotationHandler, bouncetime=50)

	def rotationHandler(self, channel):
		if GPIO.input(self.dt) == 1:
			zope.event.notify(self.right())
			logger.debug("Rotary right")
		else:
			zope.event.notify(self.left())
			logger.debug("Rotary left")

	class left(object):
		def __repr__(self):
			return self.__class__.__name__

	class right(object):
		def __repr__(self):
			return self.__class__.__name__