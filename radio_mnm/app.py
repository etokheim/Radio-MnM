import logging
from config.config import config
from datetime import datetime
import os

# Local imports
from controls import radio

logger = logging.getLogger("Radio_mnm")

radio = radio.Radio()

# Couldn't figure out how to put the error handling into the radio class.
# The problem was getting self into the logCallback function which is decorated
# by vlc. We need the radio object to get the instance and the handleError function.
# Temporarly put it here. TODO: Fix that.
import vlc
import ctypes

# Load the Windows ctypes library if Windows
if os.name == "nt":
	libc = ctypes.cdll.msvcrt
else:
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