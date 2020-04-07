import datetime
from RPi import GPIO
import time
import vlc
from datetime import datetime
import threading
import zope.event
import requests

import zope.event.classhandler

from config import config
import switches.switch1
from display import display
from controls import channels

# Button 1
pushing = False
pushStart = 0

# Button 2
button2Pushing = False

# Non-blocking interval execution
import threading

class ThreadJob(threading.Thread):
	def __init__(self,callback,event,interval):
		'''runs the callback function after interval seconds

		:param callback:  callback function to invoke
		:param event: external event for controlling the update operation
		:param interval: time in seconds after which are required to fire the callback
		:type callback: function
		:type interval: int
		'''
		self.callback = callback
		self.event = event
		self.interval = interval
		super(ThreadJob,self).__init__()

	def run(self):
		while not self.event.wait(self.interval):
			self.callback()

event = threading.Event()

# Button 2
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# I really have no idea how Zope events works, but this project is a very "learn
# as we go" project. Anyways, what I wanted to do here was to create an event system
# where I could subscribe to several events: click, down, up, longClick. This I
# figured out, but I'm still unable to pass arguments down to the event handlers.
# But as I don't need to pass down arguments yet, It's not a big problem yet. An
# example of arguments could be an event for clicking the mouse. That should resolve
# in an event, click, with arguments like pointer position x and y.

class button2Up(object):
	def __repr__(self):
		return self.__class__.__name__

def button2UpHandler(event):
	config.on = False
	print("button2UpHandler %r" % event)
	player.stop()
	display.clear()

class button2Down(object):
	def __repr__(self):
		return self.__class__.__name__

def button2DownHandler(event):
	config.on = True
	print("button2DownHandler %r" % event)

	channels.fetch()

	config.player.play()

	# \n for new line \r for moving to the beginning of current line
	display.write(">- RADIO M&M -<\n\rGot " + str(len(channels.list)) + " channels")

	# Wait 2 seconds before displaying the channel name
	# (So the user gets time to read the previous message)
	timer = threading.Timer(4, lambda:
		display.write(channels.list[config.playingChannel]["name"])
	)
	timer.start()

zope.event.classhandler.handler(button2Down, button2DownHandler)
zope.event.classhandler.handler(button2Up, button2UpHandler)



def logButtonState():
	print(button2Pushing)

# interval = ThreadJob(logButtonState,event,0.5)
# interval.start()

def run():
	global pushing, pushStart, pushStart, button2Pushing
	while True:
		time.sleep(0.01)

		button1State = GPIO.input(18)
		button2State = GPIO.input(17)

		if button1State == True and pushing == True:
			pushing = False

		# If pushing
		if button1State == False and pushStart == 0:
			pushStart = int(round(time.time() * 1000))
			pushing = True
			zope.event.notify(switches.switch1.down())

		elif pushStart != 0 and pushing == False:
			now = int(round(time.time() * 1000))
			holdTime = now - pushStart

			zope.event.notify(switches.switch1.up())
			# print("Held the button for " + str(holdTime) + " (" + str(now) + " - " + str(pushStart) + ")")
			if holdTime >= config.longClickThreshold:
				zope.event.notify(switches.switch1.longPress())
			else:
				zope.event.notify(switches.switch1.click())
			pushStart = 0
		
		# If pushing
		if button2State == False:
			if button2Pushing == False:
				# Send wake event
				zope.event.notify(button2Down())

			button2Pushing = True

		else:
			if button2Pushing == True:
				# Send sleep event
				zope.event.notify(button2Up())

			button2Pushing = False
