import os
import time
import handlers.button
import threading
from config.config import config
import logging
logger = logging.getLogger("Radio_mnm")

_ = config["getLanguage"].gettext

class NavigationButton():
	def __init__(self, radio, gpioPin):
		self.radio = radio
		self.gpioPin = gpioPin
		self.downStart = None

		self.button = handlers.button.Button(gpioPin)

		self.button.listen(self.button.click, self.buttonClickHandler)
		self.button.listen(self.button.down, self.buttonDownHandler)
		self.button.listen(self.button.up, self.buttonUpHandler)
		self.button.listen(self.button.longPress, self.buttonLongPressHandler)
		self.button.listen(self.button.veryLongPress, self.buttonVeryLongPressHandler)

	# Event is set to the the event which calls it. In this function's case it should be
	# set to "click".
	def buttonClickHandler(self, event):
		logger.debug("buttonClickHandler %r" % event)
		self.radio.bump()

	def buttonDownHandler(self, event):
		logger.debug("buttonDownHandler %r" % event)
		self.downStart = int(round(time.time() * 1000))

	def buttonUpHandler(self, event):
		logger.debug("buttonUpHandler %r" % event)
		self.downStart = 0

	def buttonLongPressHandler(self, event):
		logger.debug("buttonLongPressHandler %r" % event)
		
		# If it's less than longPressThreshold + 500 since you turned on the radio,
		# run update script.
		# Else switch to last channel
		if int(round(time.time() * 1000)) - self.radio.turnOnTime < config["longPressThreshold"] + 500:
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

	def buttonVeryLongPressHandler(self, event):
		logger.debug("VerylongPressHandler %r" % event)

		resetCountdown = self.ResetCountdown(self.radio, self.button)
		resetCountdown.start()

