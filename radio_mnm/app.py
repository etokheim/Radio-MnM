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
from switches import power
from display import display
from controls import channels

# Button 1
pushing = False
pushStart = 0

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

def run():
	global pushing, pushStart, pushStart
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
			if switches.power.pushing == False:
				# Send wake event
				zope.event.notify(switches.power.down())

			switches.power.pushing = True

		else:
			if switches.power.pushing == True:
				# Send sleep event
				zope.event.notify(switches.power.up())

			switches.power.pushing = False
