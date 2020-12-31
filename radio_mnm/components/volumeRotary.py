from handlers import rotaryMechanic
import logging
logger = logging.getLogger("Radio_mnm")

class VolumeRotary():
	def __init__(self, radio, clk, dt):
		self.radio = radio
		self.clk = clk
		self.dt = dt

		self.rotary = rotaryMechanic.Rotary(self.clk, self.dt)

		self.rotary.addEventListener("left", self.rotaryLeftHandler)
		self.rotary.addEventListener("right", self.rotaryRightHandler)

	def rotaryLeftHandler(self):
		logger.debug("Volume rotaryLeftHandler")
		self.radio.setVolume(self.radio.volume - 10)

	def rotaryRightHandler(self):
		logger.debug("Volume rotaryRightHandler")
		self.radio.setVolume(self.radio.volume + 10)
		