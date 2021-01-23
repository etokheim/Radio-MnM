from config.config import config
import logging
logger = logging.getLogger("Radio_mnm")
_ = config["getLanguage"].gettext

class EmulatedFrontend():
	def __init__(self, radio):
		self.radio = radio

		# Attach components
		if "components" in config:
			if "emulatedNavigationButton" in config["components"]:
				import components.emulatedNavigationButton as emulatedNavigationButton
				self.emulatedNavigationButton = emulatedNavigationButton.EmulatedNavigationButton(radio)
				
		# Add event listeners
		radio.addEventListener("on", self.handleOn)
		radio.addEventListener("off", self.handleOff)

	def handleOn(self):
		logger.debug("handleOn")

		# \n for new line \r for moving to the beginning of current line
		self.display.notification(">- RADIO M&M  -<\n\r" + _("Got ") + str(len(self.radio.channels)) + _(" channels"), 3)
		
		# Find a way to implement this into the buttons, if it helps with the standby mode compute.
		# button.resume()

	def handleOff(self):
		logger.debug("handleOff")
		pass