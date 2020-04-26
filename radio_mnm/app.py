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

import switches.button
from switches import power
from controls import channels
from display.display import display
from controls import setup

import threading

registration = setup.registration

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
	config.radio.bump(-1)

button.listen(button.longPress, buttonLongPressHandler)

class ResetCountdown(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.loadingBar = ""

	def run(self):
		display.notification("RESETTING RADIO\n****************")
		time.sleep(1.5)
		while button.state == "down":
			self.loadingBar = self.loadingBar + "█"
			display.notification("ARE YOU SURE?\n\r" + self.loadingBar)
			time.sleep(0.3)
			
			if len(self.loadingBar) >= 15:
				setup.reset()
				return

def buttonVeryLongPressHandler(event):
	logger.debug("VerylongPressHandler %r" % event)

	resetCountdown = ResetCountdown()
	resetCountdown.start()

button.listen(button.veryLongPress, buttonVeryLongPressHandler)



powerSwitch = switches.power.Switch(17)

def powerSwitchUpHandler(event):
	config.on = False
	logger.debug("powerSwitchUpHandler %r" % event)
	config.radio.stop()
	display.pause()
	button.pause()
	# button.resume()

powerSwitch.listen(powerSwitch.up, powerSwitchUpHandler)

def powerSwitchDownHandler(event):
	logger.debug("powerSwitchDownHandler %r" % event)
	config.on = True

	# TODO: Maybe rename .start() methods that aren't threads, as it can be confusing.
	# Starts the registration if the radio isn't registered
	registration.start()
	config.radio.fetchChannels()

	display.resume()
	button.resume()

	config.radio.play()

powerSwitch.listen(powerSwitch.down, powerSwitchDownHandler)

def run():
	display.start()
	button.start()
	powerSwitch.start()

	# If not running on a raspberry pi, fake the power button
	# to always be switched on.
	if config.raspberry == False:
		zope.event.notify(switches.power.down())
		switches.power.pushing = True