import os

debug = True

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
quality = 128

player = None

playingChannel = 0

longPressThreshold = 600
veryLongPressThreshold = 5000
on = False

checkPowerSwitchStateInterval = 0.25
checkButtonStateInterval = 0.01

apiServer = "https://127.0.0.1:8000"

# Will be set to the radio 
radio = None

# In characters, not pixels
displayWidth = 16
displayHeight = 2

# For how many steps we should pause when displaying the start of the line
displayScrollingStartPauseSteps = 12

# For how many steps we should pause when displaying the end of the line
displayScrollingStopPauseSteps = 8

# Time between scrolls
displayScrollSpeed = 0.2 # seconds