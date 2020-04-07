import vlc
import requests
from display import display
from config import config

list = None

def fetch():
	global list

	display.write("Fetching channels")

	response = requests.get("https://radio.tokheimgrafisk.no/channels")
	response = response.json()

	list = response

	config.player = vlc.MediaPlayer(list[config.playingChannel]["streams"][0])

# Bumps the channel n times. Loops around if bumping past the last channel.
def bump(bumps = 1):
	global list
	bumpTo = 0

	# Number of channels to skip which remains after removing overflow.
	# (Overflow: if you are playing channel 3 of 10 and is instructed to skip 202 channels ahead,
	# you would end up on channel 205. The overflow is 200, and we should return channel 5 (3 + 2))
	remaining = (len(list) + bumps) % len(list)

	if config.playingChannel + remaining > len(list) - 1:
		bumpTo = config.playingChannel - len(list) + remaining

	elif config.playingChannel + remaining < 0:
		bumpTo = len(list) + config.playingChannel + remaining

	else:
		bumpTo = config.playingChannel + remaining

	print("bumps " + str(bumps) + ", bumping to: " + str(bumpTo))
	set(bumpTo)

	

# Takes the parameter (int) and switches to that channel
def set(channelNumber):
	global list

	if config.on == False:
		print("Can't switch channel when radio is off!")
		return

	config.playingChannel = channelNumber

	config.player.stop()
	config.player = vlc.MediaPlayer(list[config.playingChannel]["streams"][0])
	config.player.play()

	print("Channel " + str(config.playingChannel) + " (" + list[config.playingChannel]["name"] + ")")
	
	display.write(list[config.playingChannel]["name"])
