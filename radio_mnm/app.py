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

import threading

button = switches.button.Button()
button.start()

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

def run():
	# If not running on a raspberry pi, fake the power button
	# to always be switched on.
	if config.raspberry == False:
		zope.event.notify(switches.power.down())
		switches.power.pushing = True
	
	while config.raspberry:
		time.sleep(0.01)
		
		button2State = GPIO.input(17)

		# If pushing
		if button2State == False:
			if switches.power.pushing == False:
				# Send wake event
				zope.event.notify(switches.power.down())

			switches.power.pushing = True

		else:
			if switches.power.pushing == True:
				# Send sleep event
				zope.event.notify(switches.power.up())

			switches.power.pushing = False
