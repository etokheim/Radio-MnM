import vlc
import requests
from tinydb import TinyDB, Query
import sys
import time

from display import display
from config import config

db = TinyDB('./db/db.json')
Radio = Query()
radioTable = db.table("Radio_mnm")
radio = radioTable.search(Radio)[0]

list = None

def fetch():
	global list

	display.write("Fetching streams")

	try:
		headers = { "apiKey": radio["apiKey"] }
		response = requests.get("https://127.0.0.1:8000/radio/api/1/channels?homeId=" + radio["homeId"], headers=headers, verify=False)
		status_code = response.status_code
		response = response.json()
		
		print("response (" + str(status_code) + "):")
		print(response)

		if status_code == 200:
			list = response["channels"]

			# Add channels to the database for use in case the server goes down
			radioTable.update({ "channels": list }, doc_ids=[1])
		else:
			print("Status code was " + str(status_code))
			raise Exception(response)
	except Exception:
		display.write("Failed to get\n\rchannels!")
		print(Exception)
		time.sleep(1)

		# Recover by using channels from local db instead if we have them
		channels = radio["channels"]
		print("channels ---------")
		print(channels)
		if channels:
			display.write("Using local\n\rchannels instead")
			time.sleep(1)
			list = channels
		else:
			display.write("No channels are\n\rcached, exiting")
			print("------------ EXITED ------------")
			time.sleep(1)
			# Exit with code "112, Host is down"
			sys.exit(112)

	# Start playing
	config.player = vlc.MediaPlayer(list[config.playingChannel]["streams"][0]["url"])

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
	config.player = vlc.MediaPlayer(list[config.playingChannel]["streams"][0]["url"])
	config.player.play()

	print("Channel " + str(config.playingChannel) + " (" + list[config.playingChannel]["name"] + ")")
	
	display.write(list[config.playingChannel]["name"])
