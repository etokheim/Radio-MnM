import datetime
from RPi import GPIO
# from EmulatorGUI import GPIO

import time
from datetime import datetime
import zope.event

import zope.event.classhandler

from config import config
import switches.switch
from switches import power
from display import display
from controls import channels

import threading

switch1 = switches.switch.Switch()
switch1.start()

# Event is set to the the event which calls it. In this function's case it should be
# set to "click".
def clickHandler(event):
	print("click %r" % event)

	channels.bump()

switch1.listen(switch1.click, clickHandler)


def downHandler(event):
	global downStart

	downStart = int(round(time.time() * 1000))

	print("downHandler %r" % event)

switch1.listen(switch1.down, downHandler)


def upHandler(event):
	global downStart
	
	print("upHandler %r" % event)

	downStart = 0

switch1.listen(switch1.up, upHandler)


def longPressHandler(event):
	print("longPressHandler %r" % event)
	channels.bump(-1)

switch1.listen(switch1.longPress, longPressHandler)

def run():
	while True:
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
