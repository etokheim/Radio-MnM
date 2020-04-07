from RPi import GPIO
import time
from controls import channels
from display import display
from config import config
import zope.event.classhandler
import threading

# Button 2
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

pushing = False

# I really have no idea how Zope events works, but this project is a very "learn
# as we go" project. Anyways, what I wanted to do here was to create an event system
# where I could subscribe to several events: click, down, up, longClick. This I
# figured out, but I'm still unable to pass arguments down to the event handlers.
# But as I don't need to pass down arguments yet, It's not a big problem yet. An
# example of arguments could be an event for clicking the mouse. That should resolve
# in an event, click, with arguments like pointer position x and y.

class up(object):
	def __repr__(self):
		return self.__class__.__name__

def upHandler(event):
	config.on = False
	print("powerUpHandler %r" % event)
	config.player.stop()
	display.clear()

class down(object):
	def __repr__(self):
		return self.__class__.__name__

def downHandler(event):
	config.on = True
	print("powerDownHandler %r" % event)

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

zope.event.classhandler.handler(down, downHandler)
zope.event.classhandler.handler(up, upHandler)