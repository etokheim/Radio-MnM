from handlers import rotaryPolling
import logging
logger = logging.getLogger("Radio_mnm")

class NavigationRotary():
	def __init__(self, radio, clk, dt):
		self.radio = radio
		self.clk = clk
		self.dt = dt

		self.rotary = rotaryPolling.Rotary(self.clk, self.dt)

		
		self.rotary.addEventListener("left", self.rotaryLeftHandler)
		self.rotary.addEventListener("right", self.rotaryRightHandler)

	def rotaryLeftHandler(self):
		logger.debug("Navigation rotaryLeftHandler")
		self.radio.bump(-1)

	def rotaryRightHandler(self):
		logger.debug("Navigation rotaryRightHandler")
		self.radio.bump(1)
