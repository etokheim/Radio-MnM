from handlers import rotaryPolling
import logging
logger = logging.getLogger("Radio_mnm")

class VolumeRotary():
	def __init__(self, radio, clk, dt):
		self.radio = radio
		self.clk = clk
		self.dt = dt

		self.rotary = rotaryPolling.Rotary(self.clk, self.dt)

		self.rotary.addEventListener("left", self.rotaryLeftHandler)
		self.rotary.addEventListener("right", self.rotaryRightHandler)

	def rotaryLeftHandler(self):
		logger.debug("Volume rotaryLeftHandler")
		
		if self.radio.on:
			self.radio.setVolume(self.radio.volume - 10)
			self.radio.displayVolumeLevel()

	def rotaryRightHandler(self):
		logger.debug("Volume rotaryRightHandler")
		
		if self.radio.on:
			self.radio.setVolume(self.radio.volume + 10)
			self.radio.displayVolumeLevel()
		