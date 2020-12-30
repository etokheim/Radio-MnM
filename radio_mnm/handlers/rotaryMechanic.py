import logging
logger = logging.getLogger("Radio_mnm")
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

		self.left = []
		self.right = []

		# Set up GPIO pins
		GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		# Listen for events on the CLK pin
		GPIO.add_event_detect(clk, GPIO.FALLING, callback=self.rotationHandler, bouncetime=50)

	# Loops through the callbacks parameter (array) and executes them
	def dispatch(self, callbacks):
		for callback in callbacks:
			if callback:
				callback()

	def addEventListener(self, type, callback):
		if type == "left":
			self.left.append(callback)
		elif type == "right":
			self.right.append(callback)
		else:
			raise Exception("Event type " + str(callback) + "is not supported.")

	def rotationHandler(self, channel):
		if GPIO.input(self.dt) == 1:
			self.dispatch(self.right)
			logger.debug("Rotary right")
		else:
			self.dispatch(self.left)
			logger.debug("Rotary left")
