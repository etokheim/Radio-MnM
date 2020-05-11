###################################
#                                 #
#            Overview             #
#                                 #
###################################
# The config file is a nice place to set, transform or parse values in a central place.


###################################

import os
import gettext
import logging

# Boolean environment variables has to be casted to Python booleans as they are only parsed
# as strings. A string will always evaluate to true.
def castToBool(string):
	if string == "True" or string == "true" or string == "1":
		return True
	else:
		return False

###################################
#                                 #
#              Setup              #
#                                 #
###################################
# Language
# TODO: Get language from API
nno = gettext.translation("base", localedir="locales", languages=["nno"])

debug = castToBool(os.environ["mnm_debug"])

level = os.environ["mnm_productionLogLevel"]
if level == "critical":
	productionLogLevel = logging.CRITICAL
elif level == "error":
	productionLogLevel = logging.ERROR
elif level == "warning":
	productionLogLevel = logging.WARNING
elif level == "warn":
	productionLogLevel = logging.WARNING
elif level == "info":
	productionLogLevel = logging.INFO
elif level == "debug":
	productionLogLevel = logging.DEBUG
else:
	productionLogLevel = logging.INFO

# If running on a raspberry pi, set to true
# This is a bit over simplified, but it works (just checks if the machine
# is an arm machine or not).
raspberry = False
if os.uname()[4][:3] == "arm":
	raspberry = True

longPressThreshold = 600
veryLongPressThreshold = 5000

checkPowerSwitchStateInterval = 0.25
checkButtonStateInterval = 0.01

apiServer = os.environ["mnm_apiServer"]
verifyCertificate = True


###################################
#                                 #
#              Radio              #
#                                 #
###################################
# TODO: Move radio out of the config file

# Bitrates
# Put an int in the bitrate variable, and the stream closest to that bitrate will be used.
# 32 kbps - Poor audio quality
# 48 kbps - A reasonable lower end rate for longer speech-only podcasts
# 64 kbps - A common bitrate for speech podcasts.
# 128 kbps - Common standard for musical and high quality podcasts.
# 320 kbps - Very high quality - almost indistinguishable from a CD.
bitrate = int(os.environ["mnm_bitrate"])

on = False

# Will be set to the radio 
radio = None

# Initial radio volume
volume = int(os.environ["mnm_volume"])

saveListeningHistory = castToBool(os.environ["mnm_saveListeningHistory"])

sendState = castToBool(os.environ["mnm_sendState"])


###################################
#                                 #
#             Display             #
#                                 #
###################################
# Amount of characters, not pixels
displayWidth = int(os.environ["mnm_displayWidth"])
displayHeight = int(os.environ["mnm_displayHeight"])

# Weird display quirk, where one line is two lines for the computer. I guess this is due to
# some cost saving initiative in display production.
oneDisplayLineIsTwoLines = castToBool(os.environ["mnm_oneDisplayLineIsTwoLines"])

# For how many steps we should pause when displaying the start of the line
displayScrollingStartPauseSteps = 12

# For how many steps we should pause when displaying the end of the line
displayScrollingStopPauseSteps = 8

# Time between scrolls
displayScrollSpeed = 0.2 # seconds

# Which GPIO pins the LCD pins are connected to
lcdRsToGpio			= int(os.environ["mnm_lcdRsToGpio"])
lcdEnToGpio			= int(os.environ["mnm_lcdEnToGpio"])
lcdData4ToGpio		= int(os.environ["mnm_lcdData4ToGpio"])
lcdData5ToGpio		= int(os.environ["mnm_lcdData5ToGpio"])
lcdData6ToGpio		= int(os.environ["mnm_lcdData6ToGpio"])
lcdData7ToGpio		= int(os.environ["mnm_lcdData7ToGpio"])
lcdCompatibleMode	= castToBool(os.environ["mnm_lcdCompatibleMode"])
lcdDotSize			= int(os.environ["mnm_lcdDotSize"])
lcdCharMap			= os.environ["mnm_lcdCharMap"]
