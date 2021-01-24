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
				if config["components"]["emulatedNavigationButton"]:
					import components.emulatedNavigationButton as emulatedNavigationButton
					self.emulatedNavigationButton = emulatedNavigationButton.EmulatedNavigationButton()
			
			if config["components"]["emulatedButton"]:
				import handlers.emulatedButton as emulatedButton 
				self.emulatedButton = emulatedButton.Button()

		# Add event listeners
		radio.addEventListener("on", self.handleOn)
		radio.addEventListener("off", self.handleOff)

		self.emulatedButton.addEventListener("click", lambda: print("Next channel"))
		self.emulatedButton.addEventListener("longPress", lambda: print("Previous channel"))
		self.emulatedButton.addEventListener("veryLongPress", lambda: print("Start reset sequence"))


	def handleOn(self):
		logger.debug("handleOn")

		# \n for new line \r for moving to the beginning of current line
		self.display.notification(">- RADIO M&M  -<\n\r" + _("Got ") + str(len(self.radio.channels)) + _(" channels"), 3)
		
		# Find a way to implement this into the buttons, if it helps with the standby mode compute.
		# button.resume()

	def handleOff(self):
		logger.debug("handleOff")
		pass