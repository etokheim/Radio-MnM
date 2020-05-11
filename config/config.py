import os
import gettext
import logging

def castToBool(string):
	if string == "True" or string == "true" or string == "1":
		return True
	else:
		return False

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

# Qualities
# Put a number in the quality variable, and the stream closest to that bitrate will be used.
# 32 kbps - Poor audio quality
# 48 kbps - A reasonable lower end rate for longer speech-only podcasts
# 64 kbps - A common bitrate for speech podcasts.
# 128 kbps - Common standard for musical and high quality podcasts.
# 320 kbps - Very high quality - almost indistinguishable from a CD.
bitrate = int(os.environ["mnm_bitrate"])

player = None

playingChannel = 0

longPressThreshold = 600
veryLongPressThreshold = 5000
on = False

checkPowerSwitchStateInterval = 0.25
checkButtonStateInterval = 0.01

apiServer = os.environ["mnm_apiServer"]
verifyCertificate = "https://radio.tokheimgrafisk.no" == apiServer

# Will be set to the radio 
radio = None

# In characters, not pixels
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

# Initial radio volume
volume = int(os.environ["mnm_volume"])