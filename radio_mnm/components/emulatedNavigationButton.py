import os
import time
import handlers.button
import threading
from config.config import config
import logging
logger = logging.getLogger("Radio_mnm")

_ = config["getLanguage"].gettext

class EmulatedNavigationButton():
	def __init__(self, radio):
		self.radio = radio
		self.downStart = None

		self.button = handlers.emulatedButton.EmulatedButton()

		self.button.addEventListener("click", self.buttonClickHandler)
		self.button.addEventListener("press", self.buttonDownHandler)
		self.button.addEventListener("release", self.buttonUpHandler)
		self.button.addEventListener("longPress", self.buttonLongPressHandler)
		self.button.addEventListener("veryLongPress", self.buttonVeryLongPressHandler)

	# Event is set to the the event which calls it. In this function's case it should be
	# set to "click".
	def buttonClickHandler(self):
		logger.debug("navigationButtonClickHandler (" + str(self.gpioPin) + ")")
		self.radio.bump()

	def buttonDownHandler(self):
		logger.debug("navigationButtonDownHandler (" + str(self.gpioPin) + ")")
		self.downStart = int(round(time.time() * 1000))

	def buttonUpHandler(self):
		logger.debug("navigationButtonUpHandler (" + str(self.gpioPin) + ")")
		self.downStart = 0

	def buttonLongPressHandler(self):
		logger.debug("navigationButtonLongPressHandler (" + str(self.gpioPin) + ")")
		
		# If it's less than longPressThreshold + 500 since you turned on the radio,
		# run update script.
		# Else switch to last channel
		if int(round(time.time() * 1000)) - self.radio.powerOnTime < config["longPressThreshold"] + 500:
			self.radio.updating = {
				"code": "updating",
				"text": _("Updating, don't pull the plug!")
			}
			self.radio.display.notification(_("Updating (15min)\r\nDon't pull the plug!"), 5)

			# Run the update from another thread, so the radio keeps responding to input
			thread = threading.Thread(target = os.system, args = ("sudo scripts/update.sh", ))
			thread.start()
		else:
			self.radio.bump(-1)


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

	def buttonVeryLongPressHandler(self):
		logger.debug("VerylongPressHandler")

		resetCountdown = self.ResetCountdown(self.radio, self.button)
		resetCountdown.start()

