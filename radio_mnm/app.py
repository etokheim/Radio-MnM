import logging
logger = logging.getLogger("Radio_mnm")
from config import config

if config.raspberry == True:
	from RPi import GPIO
else:
	from EmulatorGUI.EmulatorGUI import GPIO

import datetime
import time
from datetime import datetime
import zope.event
import zope.event.classhandler
import threading
import gettext
import os

import switches.button
import switches.power
from controls import radio

config.nno.install()
_ = config.nno.gettext

button = switches.button.Button(18)

# Event is set to the the event which calls it. In this function's case it should be
# set to "click".
def buttonClickHandler(event):
	logger.debug("buttonClickHandler %r" % event)

	config.radio.bump()

button.listen(button.click, buttonClickHandler)


def buttonDownHandler(event):
	global downStart

	downStart = int(round(time.time() * 1000))

	logger.debug("buttonDownHandler %r" % event)

button.listen(button.down, buttonDownHandler)


def buttonUpHandler(event):
	global downStart
	
	logger.debug("buttonUpHandler %r" % event)

	downStart = 0

button.listen(button.up, buttonUpHandler)


def buttonLongPressHandler(event):
	logger.debug("buttonLongPressHandler %r" % event)
	
	# If it's less than longPressThreshold + 500 since you turned on the radio,
	# run update script.
	# Else switch to last channel
	if int(round(time.time() * 1000)) - config.radio.turnOnTime < config.longPressThreshold + 500:
		config.radio.display.notification("Updating (15min)\r\nDon't pull the plug!", 5)
		config.radio.state = {
			"code": "updating",
			"text": _("Updating, don't pull the plug!")
		}
		os.system("sudo scripts/update.sh")
	else:
		config.radio.bump(-1)

button.listen(button.longPress, buttonLongPressHandler)

class ResetCountdown(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.loadingBar = ""

	def run(self):
		config.radio.display.notification(_("RESETTING RADIO") + "\n****************")
		time.sleep(1.5)
		# Add the text to a variable so we only have to translate it once.
		confirmText = _("ARE YOU SURE?")
		confirmTextLength = len(confirmText)
		config.radio.display.notification(confirmText)
		time.sleep(0.3)

		while button.state == "down":
			self.loadingBar = self.loadingBar + "*"
			# self.loadingBar = self.loadingBar + "█"
			if config.radio.display.displayHeight == 1:
				config.radio.display.notification(self.loadingBar + confirmText[len(self.loadingBar) : confirmTextLength])
			else: 
				config.radio.display.notification(confirmText + "\n\r" + self.loadingBar)
			
			# Sleeping shorter than 0.3 seconds seems to make the display go corrupt...
			time.sleep(0.3)
			# time.sleep(3 / config.radio.display.displayWidth)
			
			if len(self.loadingBar) >= config.radio.display.displayWidth:
				config.radio.registration.reset()
				return

def buttonVeryLongPressHandler(event):
	logger.debug("VerylongPressHandler %r" % event)

	resetCountdown = ResetCountdown()
	resetCountdown.start()

button.listen(button.veryLongPress, buttonVeryLongPressHandler)



powerSwitch = switches.power.Switch(17)

def powerSwitchUpHandler(event):
	logger.debug("powerSwitchUpHandler %r" % event)
	
	# TODO: Most of this should go into a radio.off() method.
	config.radio.on = False
	config.radio.stop()
	config.radio.display.pause()
	button.pause()
	config.radio.handleSendState("suspended")

	# I'm not quite sure I have to reset all of these values
	config.radio.display.currentlyDisplayingMessage = ""
	config.radio.display.notificationMessage = ""
	config.radio.display.lastDisplayedMessage = ""
	config.radio.display.lastDisplayedCroppedMessage = ""

powerSwitch.listen(powerSwitch.up, powerSwitchUpHandler)

def powerSwitchDownHandler(event):
	logger.debug("powerSwitchDownHandler %r" % event)

	# TODO: Most of this should go into a radio.on() method.
	config.radio.on = True
	config.radio.display.resume()
	button.resume()

	config.radio.turnOnTime = int(round(time.time() * 1000))

	# TODO: Maybe rename .start() methods that aren't threads, as it can be confusing.
	# Starts the registration if the radio isn't registered
	config.radio.registration.start()
	
	if config.radio.lastPowerState != "off":
		config.radio.handleSendState("noPower")

	config.radio.handleSendState("on")

	if len(config.radio.channels) > 0:
		config.radio.play()

powerSwitch.listen(powerSwitch.down, powerSwitchDownHandler)

def run():
	config.radio.display.start()
	button.start()
	powerSwitch.start()

	# If not running on a raspberry pi, fake the power button
	# to always be switched on.
	if config.raspberry == False:
		zope.event.notify(switches.power.down())
		switches.power.pushing = True