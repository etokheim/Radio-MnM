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
from display import display
from controls import channels
from controls import setup

import threading

registration = setup.registration

button = switches.button.Button(18)

# Event is set to the the event which calls it. In this function's case it should be
# set to "click".
def buttonClickHandler(event):
	print("click %r" % event)

	channels.bump()

button.listen(button.click, buttonClickHandler)


def buttonDownHandler(event):
	global downStart

	downStart = int(round(time.time() * 1000))

	print("downHandler %r" % event)

button.listen(button.down, buttonDownHandler)


def buttonUpHandler(event):
	global downStart
	
	print("upHandler %r" % event)

	downStart = 0

button.listen(button.up, buttonUpHandler)


def buttonLongPressHandler(event):
	print("longPressHandler %r" % event)
	channels.bump(-1)

button.listen(button.longPress, buttonLongPressHandler)

class ResetCountdown(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.loadingBar = ""

	def run(self):
		display.write("RESETTING RADIO\n****************")
		time.sleep(1.5)
		while button.state == "down":
			self.loadingBar = self.loadingBar + "█"
			display.write("ARE YOU SURE?\n\r" + self.loadingBar)
			time.sleep(0.3)
			
			if len(self.loadingBar) >= 15:
				setup.reset()
				return

def buttonVeryLongPressHandler(event):
	print("VerylongPressHandler %r" % event)

	resetCountdown = ResetCountdown()
	resetCountdown.start()
	


button.listen(button.veryLongPress, buttonVeryLongPressHandler)

powerSwitch = switches.power.Switch(17)

def powerSwitchUpHandler(event):
	config.on = False
	print("powerSwitchUpHandler %r" % event)
	config.player.stop()
	display.clear()

powerSwitch.listen(powerSwitch.up, powerSwitchUpHandler)

def powerSwitchDownHandler(event):
	config.on = True
	print("powerSwitchDownHandler %r" % event)

	channels.fetch()

	config.player.play()

	# \n for new line \r for moving to the beginning of current line
	display.write(">- RADIO M&M -<\n\rGot " + str(len(channels.list)) + " channels")

	# Wait 4 seconds before displaying the channel name
	# (So the user gets time to read the previous message)
	timer = threading.Timer(4, lambda:
		display.write(channels.list[config.playingChannel]["name"])
	)
	timer.start()

powerSwitch.listen(powerSwitch.down, powerSwitchDownHandler)

def run():
	# Starts the registration if the radio isn't registered
	registration.start()
	button.start()
	powerSwitch.start()

	# If not running on a raspberry pi, fake the power button
	# to always be switched on.
	if config.raspberry == False:
		zope.event.notify(switches.power.down())
		switches.power.pushing = True