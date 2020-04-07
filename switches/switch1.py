from RPi import GPIO
import time
from controls import channels
import zope.event.classhandler

downStart = 0

GPIO.setmode(GPIO.BCM)

# Button 1
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

class click(object):
	def __repr__(self):
		return self.__class__.__name__

# Event is set to the the event which calls it. In this function's case it should be
# set to "click".
def clickHandler(event):
	print("click %r" % event)

	channels.bump()


class down(object):
	def __repr__(self):
		return self.__class__.__name__

def downHandler(event):
	global downStart

	downStart = int(round(time.time() * 1000))

	print("downHandler %r" % event)

class up(object):
	def __repr__(self):
		return self.__class__.__name__

def upHandler(event):
	global downStart
	
	print("upHandler %r" % event)

	downStart = 0

class longPress(object):
	def __repr__(self):
		return self.__class__.__name__

def longPressHandler(event):
	print("longPressHandler %r" % event)
	channels.bump(-1)

zope.event.classhandler.handler(longPress, longPressHandler)
zope.event.classhandler.handler(up, upHandler)
zope.event.classhandler.handler(down, downHandler)
zope.event.classhandler.handler(click, clickHandler)