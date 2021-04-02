import logging
logger = logging.getLogger("Radio_mnm")
from RPi import GPIO
import asyncio

GPIO.setmode(GPIO.BCM)
	
class Rotary():
	def __init__(self, clk, dt):
		self.clk = clk
		self.dt = dt

		self.left = []
		self.right = []

		self.loop = asyncio.get_event_loop()

		# Set up GPIO pins
		GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		# Listen for events on the CLK pin
		GPIO.add_event_detect(clk, GPIO.FALLING, callback=self.rotationHandler, bouncetime=80)

	# Loops through the callbacks parameter (array) and executes them
	async def dispatch(self, callbacks):
		for callback in callbacks:
			if callback:
				if callback[1]:
					args = callback[1]
					callback[0](*args)
				else:
					callback[0]()

	def addEventListener(self, type, callback, args=[]):
		if type == "left":
			self.left.append([callback, args])
		elif type == "right":
			self.right.append([callback, args])
		else:
			raise Exception("Event type " + str(callback) + "is not supported.")

	def rotationHandler(self, channel):
		if GPIO.input(self.dt) == 1:
			logger.debug("Rotary right (GPIO " + str(self.clk) + " and " + str(self.dt) + ")")
			asyncio.run_coroutine_threadsafe(self.dispatch(self.right), self.loop)
		else:
			logger.debug("Rotary left (GPIO " + str(self.clk) + " and " + str(self.dt) + ")")
			asyncio.run_coroutine_threadsafe(self.dispatch(self.left), self.loop)