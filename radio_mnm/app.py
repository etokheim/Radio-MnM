import logging
logger = logging.getLogger("Radio_mnm")
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
import threading
import gettext
import os

import switches.button
import switches.rotaryMechanic
from controls import radio
from display import display
import components.powerSwitch

radio = radio.Radio()

# Consider moving this logic into the radio module
radio.display = display.Display(radio)
radio.powerSwitch = components.powerSwitch.PowerSwitch(radio, 17)

# Couldn't figure out how to put the error handling into the radio class.
# The problem was getting self into the logCallback function which is decorated
# by vlc. We need the radio object to get the instance and the handleError function.
# Temporarly put it here. TODO: Fix that.
import vlc
import ctypes

libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
vsnprintf = libc.vsnprintf

vsnprintf.restype = ctypes.c_int
vsnprintf.argtypes = (
	ctypes.c_char_p,
	ctypes.c_size_t,
	ctypes.c_char_p,
	ctypes.c_void_p,
)
# Catch the VLC logs and output them to our logs aswell
@vlc.CallbackDecorators.LogCb
def logCallback(data, level, ctx, fmt, args):
	# Skip if level is lower than error
	# TODO: Try to solve as many warnings as possible
	if level < 4:
		return

	# Format given fmt/args pair
	BUF_LEN = 1024
	outBuf = ctypes.create_string_buffer(BUF_LEN)
	vsnprintf(outBuf, BUF_LEN, fmt, args)

	# Transform to ascii string
	log = outBuf.raw.decode('ascii').strip().strip('\x00')

	# Handle any errors
	if level > 3:
		shouldLog = radio.handleError(log)

		# If noisy error, then don't log it
		if not shouldLog:
			return

	# Output vlc logs to our log
	if level == 5:
		logger.critical(log)
	elif level == 4:
		logger.error(log)
	elif level == 3:
		logger.warning(log)
	elif level == 2:
		logger.info(log)

radio.instance.log_set(logCallback, None)

config.nno.install()
_ = config.nno.gettext

button = switches.button.Button(8)
rotary = switches.rotaryMechanic.Rotary(20, 12, 16)

def rotaryLeft(event):
	print("Rotary event left")
	radio.bump()

def rotaryRight(event):
	print("Rotary event right")
	radio.bump(-1)

rotary.listen(rotary.left, rotaryLeft)
rotary.listen(rotary.right, rotaryRight)

# Event is set to the the event which calls it. In this function's case it should be
# set to "click".
def buttonClickHandler(event):
	logger.debug("buttonClickHandler %r" % event)

	radio.bump()

button.listen(button.click, buttonClickHandler)


def buttonDownHandler(event):
	global downStart

	downStart = int(round(time.time() * 1000))

	logger.debug("buttonDownHandler %r" % event)

button.listen(button.down, buttonDownHandler)


def buttonUpHandler(event):
	global downStart
	
	logger.debug("buttonUpHandler %r" % event)

	downStart = 0

button.listen(button.up, buttonUpHandler)


def buttonLongPressHandler(event):
	logger.debug("buttonLongPressHandler %r" % event)
	
	# If it's less than longPressThreshold + 500 since you turned on the radio,
	# run update script.
	# Else switch to last channel
	if int(round(time.time() * 1000)) - radio.turnOnTime < config.longPressThreshold + 500:
		radio.updating = {
			"code": "updating",
			"text": _("Updating, don't pull the plug!")
		}
		radio.display.notification(_("Updating (15min)\r\nDon't pull the plug!"), 5)

		# Run the update from another thread, so the radio keeps responding to input
		thread = threading.Thread(target = os.system, args = ("sudo scripts/update.sh", ))
		thread.start()
	else:
		radio.bump(-1)

button.listen(button.longPress, buttonLongPressHandler)

class ResetCountdown(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.loadingBar = ""

	def run(self):
		radio.display.notification(_("RESETTING RADIO") + "\n****************")
		time.sleep(1.5)
		# Add the text to a variable so we only have to translate it once.
		confirmText = _("ARE YOU SURE?")
		confirmTextLength = len(confirmText)
		radio.display.notification(confirmText)
		time.sleep(0.3)

		while button.state == "down":
			self.loadingBar = self.loadingBar + "*"
			# self.loadingBar = self.loadingBar + "█"
			if radio.display.displayHeight == 1:
				radio.display.notification(self.loadingBar + confirmText[len(self.loadingBar) : confirmTextLength])
			else: 
				radio.display.notification(confirmText + "\n\r" + self.loadingBar)
			
			# Sleeping shorter than 0.3 seconds seems to make the display go corrupt...
			time.sleep(0.3)
			# time.sleep(3 / radio.display.displayWidth)
			
			if len(self.loadingBar) >= radio.display.displayWidth:
				radio.registration.reset()
				return

def buttonVeryLongPressHandler(event):
	logger.debug("VerylongPressHandler %r" % event)

	resetCountdown = ResetCountdown()
	resetCountdown.start()

button.listen(button.veryLongPress, buttonVeryLongPressHandler)





def run():
	radio.display.start()
	button.start()

	# If not running on a raspberry pi, fake the power button
	# to always be switched on.
	if config.raspberry == False:
		zope.event.notify(switches.power.down())
		switches.power.pushing = True