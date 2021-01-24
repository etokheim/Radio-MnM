from config.config import config
import threading
import time
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
					import handlers.emulatedButton as emulatedButton
					self.emulatedNavigationButton = emulatedButton.Button()
			
		# Add event listeners
		radio.addEventListener("on", self.handleOn)
		radio.addEventListener("off", self.handleOff)

		self.emulatedNavigationButton.addEventListener("click", lambda: print("Next channel"))
		self.emulatedNavigationButton.addEventListener("longPress", lambda: print("Previous channel"))
		self.emulatedNavigationButton.addEventListener("veryLongPress", lambda: print("Start reset sequence"))

	def handleOn(self):
		logger.debug("handleOn")

		# \n for new line \r for moving to the beginning of current line
		self.display.notification(">- RADIO M&M  -<\n\r" + _("Got ") + str(len(self.radio.channels)) + _(" channels"), 3)
		
		# Find a way to implement this into the buttons, if it helps with the standby mode compute.
		# button.resume()

	def handleOff(self):
		logger.debug("handleOff")
		pass

	class ResetCountdown(threading.Thread):
		def __init__(self, radio, button):
			threading.Thread.__init__(self)
			self.loadingBar = ""
			self.radio = radio
			self.button = button

		def run(self):
			self.radio.display.notification(_("RESETTING RADIO") + "\n****************")
			time.sleep(1.5)
			# Add the text to a variable so we only have to translate it once.
			confirmText = _("ARE YOU SURE?")
			confirmTextLength = len(confirmText)
			self.radio.display.notification(confirmText)
			time.sleep(0.3)

			while self.button.state == "down":
				self.loadingBar = self.loadingBar + "*"
				# self.loadingBar = self.loadingBar + "█"
				if self.radio.display.displayHeight == 1:
					self.radio.display.notification(self.loadingBar + confirmText[len(self.loadingBar) : confirmTextLength])
				else: 
					self.radio.display.notification(confirmText + "\n\r" + self.loadingBar)
				
				# Sleeping shorter than 0.3 seconds seems to make the display go corrupt...
				time.sleep(0.3)
				# time.sleep(3 / self.radio.display.displayWidth)
				
				if len(self.loadingBar) >= self.radio.display.displayWidth:
					self.radio.registration.reset()
					return