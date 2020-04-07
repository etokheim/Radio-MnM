import datetime
from RPi import GPIO
import time
from datetime import datetime
import zope.event

import zope.event.classhandler

from config import config
import switches.switch1
from switches import power
from display import display
from controls import channels

# Event is set to the the event which calls it. In this function's case it should be
# set to "click".
def clickHandler(event):
	print("click %r" % event)

	channels.bump()

zope.event.classhandler.handler(switches.switch1.click, clickHandler)


def downHandler(event):
	global downStart

	downStart = int(round(time.time() * 1000))

	print("downHandler %r" % event)

zope.event.classhandler.handler(switches.switch1.down, downHandler)


def upHandler(event):
	global downStart
	
	print("upHandler %r" % event)

	downStart = 0

zope.event.classhandler.handler(switches.switch1.up, upHandler)


def longPressHandler(event):
	print("longPressHandler %r" % event)
	channels.bump(-1)

zope.event.classhandler.handler(switches.switch1.longPress, longPressHandler)


def run():
	while True:
		time.sleep(0.01)

		button1State = GPIO.input(18)
		button2State = GPIO.input(17)

		if button1State == True and switches.switch1.pushing == True:
			switches.switch1.pushing = False

		# If switches.switch1.pushing
		if button1State == False and switches.switch1.pushStart == 0:
			switches.switch1.pushStart = int(round(time.time() * 1000))
			switches.switch1.pushing = True
			zope.event.notify(switches.switch1.down())

		elif switches.switch1.pushStart != 0 and switches.switch1.pushing == False:
			now = int(round(time.time() * 1000))
			holdTime = now - switches.switch1.pushStart

			zope.event.notify(switches.switch1.up())
			if holdTime >= config.longClickThreshold:
				zope.event.notify(switches.switch1.longPress())
			else:
				zope.event.notify(switches.switch1.click())
			switches.switch1.pushStart = 0
		
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
