from handlers import rotaryPolling
from validator import validate
import logging
logger = logging.getLogger("Radio_mnm")

class NavigationRotary():
	def __init__(self, radio, props):
		# Check props
		assert type(props["GPIO"]["clk"]) == int, "NavigationRotary's clk pin is not an int. Check your config.yml"
		assert type(props["GPIO"]["data"]) == int, "NavigationRotary's data pin is not an int. Check your config.yml"
		
		self.radio = radio
		self.clk = props["GPIO"]["clk"]
		self.data = props["GPIO"]["data"]

		self.rotary = rotaryPolling.Rotary(self.clk, self.data)
		self.rotary.addEventListener("left", self.rotaryLeftHandler)
		self.rotary.addEventListener("right", self.rotaryRightHandler)

	def rotaryLeftHandler(self):
		logger.debug("Navigation rotaryLeftHandler")
		self.radio.bump(-1)

	def rotaryRightHandler(self):
		logger.debug("Navigation rotaryRightHandler")
		self.radio.bump(1)
