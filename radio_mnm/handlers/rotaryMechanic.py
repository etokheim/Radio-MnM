import logging
logger = logging.getLogger("Radio_mnm")
from RPi import GPIO
	
class Rotary():
	def __init__(self, clk, dt):
		self.clk = clk
		self.dt = dt

		self.left = []
		self.right = []

		# Set up GPIO pins
		GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		# Listen for events on the CLK pin
		GPIO.add_event_detect(clk, GPIO.FALLING, callback=self.rotationHandler, bouncetime=80)

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
			logger.debug("Rotary right (GPIO " + str(self.clk) + " and " + str(self.dt) + ")")
			self.dispatch(self.right)
		else:
			logger.debug("Rotary left (GPIO " + str(self.clk) + " and " + str(self.dt) + ")")
			self.dispatch(self.left)
