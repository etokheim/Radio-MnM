import logging
logger = logging.getLogger("Radio_mnm")
import threading
from RPi import GPIO
import time

GPIO.setmode(GPIO.BCM)
	
class Rotary(threading.Thread):
	def __init__(self, clk, dt):
		threading.Thread.__init__(self)
		
		self.clk = clk
		self.dt = dt
		self.lastClkState = 1

		self.running = True
		# When paused is set, the thread will run, when it's not set, the thread will wait
		self.pauseEvent = threading.Event()

		self.left = []
		self.right = []

		# Set up GPIO pins
		GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		# Listen for events on the CLK pin
		# GPIO.add_event_detect(clk, GPIO.FALLING, callback=self.rotationHandler, bouncetime=50)
		self.start()

	# Loops through the callbacks parameter (array) and executes them
	def dispatch(self, callbacks):
		for callback in callbacks:
			if callback:
				if callback[1]:
					args = callback[1]
					callback[0](*args)
				else:
					callback[0]()

	def addEventListener(self, type, callback, args = []):
		if type == "left":
			self.left.append([callback, args])
		elif type == "right":
			self.right.append([callback, args])
		else:
			raise Exception("Event type " + str(callback) + "is not supported.")

	def rotationHandler(self):
		if GPIO.input(self.dt) == 1:
			logger.debug("Rotary right (GPIO " + str(self.clk) + " and " + str(self.dt) + ")")
			self.dispatch(self.right)
		else:
			logger.debug("Rotary left (GPIO " + str(self.clk) + " and " + str(self.dt) + ")")
			self.dispatch(self.left)

	def run(self):
		while self.running:
			time.sleep(0.01)

			clkState = GPIO.input(self.clk)

			# If pushing
			if clkState == False and self.lastClkState:
				self.rotationHandler()

			self.lastClkState = clkState

	def stop(self):
		self.running = False
		logger.warning("Stopped listening to the power switch")