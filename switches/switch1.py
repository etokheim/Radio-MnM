from RPi import GPIO
import time
from controls import channels
import zope.event.classhandler
from threading import Thread
from switches import switch1
from config import config

pushing = False
pushStart = 0
downStart = 0

GPIO.setmode(GPIO.BCM)

# Button 1
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

class click(object):
	def __repr__(self):
		return self.__class__.__name__


class down(object):
	def __repr__(self):
		return self.__class__.__name__

class up(object):
	def __repr__(self):
		return self.__class__.__name__

class longPress(object):
	def __repr__(self):
		return self.__class__.__name__


class MonitorSwitch(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.running = True

	def run(self):
		while self.running:
			time.sleep(0.01)

			button1State = GPIO.input(18)

			if button1State == True and switch1.pushing == True:
				switch1.pushing = False

			# If switch1.pushing
			if button1State == False and switch1.pushStart == 0:
				switch1.pushStart = int(round(time.time() * 1000))
				switch1.pushing = True
				zope.event.notify(switch1.down())

			elif switch1.pushStart != 0 and switch1.pushing == False:
				now = int(round(time.time() * 1000))
				holdTime = now - switch1.pushStart

				zope.event.notify(switch1.up())
				if holdTime >= config.longClickThreshold:
					zope.event.notify(switch1.longPress())
				else:
					zope.event.notify(switch1.click())
				switch1.pushStart = 0

	def stop(self):
		self.running = False

a = MonitorSwitch()

a.start()
