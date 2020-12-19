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
import switches.rotaryMechanic
import switches.power
from controls import radio
from display import display

radio = radio.Radio()

radio.display = display.Display(radio)

config.nno.install()
_ = config.nno.gettext

button = switches.button.Button(8)
rotary = switches.rotaryMechanic.Rotary(20, 12, 16)

def rotaryLeft(event):
	print("Rotary event left")
	radio.bump()

def rotaryRight(event):
	print("Rotary event right")
	radio.bump(-1)

rotary.listen(rotary.left, rotaryLeft)
rotary.listen(rotary.right, rotaryRight)

# Event is set to the the event which calls it. In this function's case it should be
# set to "click".
def buttonClickHandler(event):
	logger.debug("buttonClickHandler %r" % event)

	radio.bump()

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
	if int(round(time.time() * 1000)) - radio.turnOnTime < config.longPressThreshold + 500:
		radio.updating = {
			"code": "updating",
			"text": _("Updating, don't pull the plug!")
		}
		radio.display.notification(_("Updating (15min)\r\nDon't pull the plug!"), 5)

		# Run the update from another thread, so the radio keeps responding to input
		thread = threading.Thread(target = os.system, args = ("sudo scripts/update.sh", ))
		thread.start()
	else:
		radio.bump(-1)

button.listen(button.longPress, buttonLongPressHandler)

class ResetCountdown(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.loadingBar = ""

	def run(self):
		radio.display.notification(_("RESETTING RADIO") + "\n****************")
		time.sleep(1.5)
		# Add the text to a variable so we only have to translate it once.
		confirmText = _("ARE YOU SURE?")
		confirmTextLength = len(confirmText)
		radio.display.notification(confirmText)
		time.sleep(0.3)

		while button.state == "down":
			self.loadingBar = self.loadingBar + "*"
			# self.loadingBar = self.loadingBar + "█"
			if radio.display.displayHeight == 1:
				radio.display.notification(self.loadingBar + confirmText[len(self.loadingBar) : confirmTextLength])
			else: 
				radio.display.notification(confirmText + "\n\r" + self.loadingBar)
			
			# Sleeping shorter than 0.3 seconds seems to make the display go corrupt...
			time.sleep(0.3)
			# time.sleep(3 / radio.display.displayWidth)
			
			if len(self.loadingBar) >= radio.display.displayWidth:
				radio.registration.reset()
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
	radio.on = False
	radio.stop()
	radio.display.pause()
	button.pause()
	radio.handleSendState("suspended")

	# I'm not quite sure I have to reset all of these values
	radio.display.currentlyDisplayingMessage = ""
	radio.display.notificationMessage = ""
	radio.display.lastDisplayedMessage = ""
	radio.display.lastDisplayedCroppedMessage = ""

powerSwitch.listen(powerSwitch.up, powerSwitchUpHandler)

def powerSwitchDownHandler(event):
	logger.debug("powerSwitchDownHandler %r" % event)

	# TODO: Most of this should go into a radio.on() method.
	radio.on = True
	radio.display.resume()
	button.resume()

	radio.turnOnTime = int(round(time.time() * 1000))

	# TODO: Maybe rename .start() methods that aren't threads, as it can be confusing.
	# Starts the registration if the radio isn't registered
	radio.registration.start()
	
	if radio.lastPowerState != "off":
		radio.handleSendState("noPower")

	radio.handleSendState("on")

	if len(radio.channels) > 0:
		radio.play()

powerSwitch.listen(powerSwitch.down, powerSwitchDownHandler)

def run():
	radio.display.start()
	button.start()
	powerSwitch.start()

	# If not running on a raspberry pi, fake the power button
	# to always be switched on.
	if config.raspberry == False:
		zope.event.notify(switches.power.down())
		switches.power.pushing = True