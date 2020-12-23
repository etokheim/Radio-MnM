import logging
logger = logging.getLogger("Radio_mnm")
from config.config import config
from RPi import GPIO
import datetime
import time
from datetime import datetime
import zope.event
import zope.event.classhandler
import threading
import gettext
import os

import handlers.rotaryMechanic
from controls import radio
import components.displayCharacterLcd as display
import components.powerSwitch as powerSwitch
import components.navigationButton as navigationButton
import components.volumeRotary as volumeRotary

radio = radio.Radio()

# Consider moving this logic into the radio module
radio.display = display.Display(radio, config["components"]["displays"][0])
radio.powerSwitch = powerSwitch.PowerSwitch(radio, 17)
radio.navigationButton = navigationButton.NavigationButton(radio, 8)
radio.volumeRotary = volumeRotary.VolumeRotary(radio, 20, 12)

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

# Called from __main__
def run():
	radio.display.start()