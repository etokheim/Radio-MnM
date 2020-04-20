from RPi import GPIO
# from EmulatorGUI import GPIO
import time
from controls import channels
import zope.event.classhandler
from threading import Thread
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


class Switch(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.running = True

		# Add class handlers
		self.click = click
		self.down = down
		self.up = up
		self.longPress = longPress

		self.pushing = False
		self.pushStart = 0
		self.downStart = 0

		self.listen = zope.event.classhandler.handler

	# Use Switch.start(), now Switch.run() to start thread
	def run(self):
		while self.running:
			time.sleep(0.01)

			button1State = GPIO.input(18)

			if button1State == True and self.pushing == True:
				self.pushing = False

			# If self.pushing
			if button1State == False and self.pushStart == 0:
				self.pushStart = int(round(time.time() * 1000))
				self.pushing = True
				zope.event.notify(self.down())

			elif self.pushStart != 0 and self.pushing == False:
				now = int(round(time.time() * 1000))
				holdTime = now - self.pushStart

				zope.event.notify(self.up())
				if holdTime >= config.longClickThreshold:
					zope.event.notify(self.longPress())
				else:
					zope.event.notify(self.click())

				self.pushStart = 0

	def stop(self):
		self.running = False
		print("Stopped switch1 monitoring thread")