from handlers import rotaryMechanic
import logging
logger = logging.getLogger("Radio_mnm")

class VolumeRotary():
	def __init__(self, radio, clk, dt):
		self.radio = radio
		self.clk = clk
		self.dt = dt

		self.rotary = rotaryMechanic.Rotary(self.clk, self.dt)

		self.rotary.listen(self.rotary.left, self.rotaryLeftHandler)
		self.rotary.listen(self.rotary.right, self.rotaryRightHandler)

	def rotaryLeftHandler(self, event):
		logger.debug("rotaryLeftHandler %r" % event)
		self.radio.setVolume(self.radio.volume - 10)

	def rotaryRightHandler(self, event):
		logger.debug("rotaryRightHandler %r" % event)
		self.radio.setVolume(self.radio.volume + 10)
		