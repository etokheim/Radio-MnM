import vlc
import requests
from tinydb import TinyDB, Query
import sys
import time

from display import display
from config import config
from controls import setup

class Radio():
	def __init__(self):
		print("New player")
		self.channels = []
		self.instance = vlc.Instance()
		self.player = self.instance.media_player_new()
		self.media = None
		self.selectedChannel = None

	def playChannel(self, channel):
		self.selectedChannel = channel
		bestBitrateMatch = self.getBestBitRateMatch(channel["streams"])
		print("Playing channel with a bitrate of " + str(channel["streams"][bestBitrateMatch]["bitrate"]) + "kbps")

		self.player.stop()
		print(bestBitrateMatch)
		url = channel["streams"][bestBitrateMatch]["url"]
		print(url)
		self.media = self.instance.media_new(url)
		self.player.set_media(self.media)
		self.player.play()

		time.sleep(1)
		print(self.media.get_meta(0))
		print(self.media.get_meta(12))

	def play(self):
		# print("Playing channel with a bitrate of " + str(self.channels[self.selectedChannel]["streams"][bestBitrateMatch]["bitrate"]) + "kbps")
		print("Playing channel")
		self.player.play()
	
	def fetchChannels(self):
		db = TinyDB('./db/db.json')
		Radio = Query()
		radioTable = db.table("Radio_mnm")
		radio = radioTable.search(Radio)[0]

		display.notification("Fetching streams")

		try:
			headers = { "apiKey": radio["apiKey"] }
			response = requests.get(config.apiServer + "/radio/api/1/channels?homeId=" + radio["homeId"], headers=headers, verify=False)
			status_code = response.status_code
			response = response.json()
			
			print("response (" + str(status_code) + "):")
			print(response)

			if status_code == 200:
				self.channels = response["channels"]

				# Add channels to the database for use in case the server goes down
				radioTable.update({ "channels": self.channels }, doc_ids=[1])
			else:
				print("Status code was " + str(status_code))
				raise Exception(response, status_code)
		except Exception:
			display.notification("Failed to get\n\rchannels!")
			time.sleep(2)
			print("Exception's status code was " + str(status_code))
			print(Exception)
			
			if status_code == 410:
				display.notification("This radio was\n\runregistered!")
				time.sleep(3)
				display.notification("Resetting radio\n\rin three seconds")
				setup.reset()
				return

			# Recover by using channels from local db instead if we have them
			channels = radio["channels"]
			if channels:
				display.notification("Using local\n\rchannels instead")
				time.sleep(1)
				self.channels = channels
			else:
				display.notification("No channels are\n\rcached, exiting")
				print("------------ EXITED ------------")
				time.sleep(1)
				# Exit with code "112, Host is down"
				sys.exit(112)

		# Only set selectedChannel if it's not set
		self.selectedChannel = self.channels[0]

		besetBitrateMatch = self.getBestBitRateMatch(self.channels[0]["streams"])
		self.media = self.instance.media_new(self.channels[0]["streams"][besetBitrateMatch]["url"])
		self.player.play()

		# Start playing
		
		# config.player = vlc.MediaPlayer(self.channels[self.selectedChannel]["streams"][bestBitrateMatch]["url"])

	# Bumps the channel n times. Loops around if bumping past the last channel.
	def bump(self, bumps = 1):
		bumpTo = 0

		# Number of channels to skip which remains after removing overflow.
		# (Overflow: if you are playing channel 3 of 10 and is instructed to skip 202 channels ahead,
		# you would end up on channel 205. The overflow is 200, and we should return channel 5 (3 + 2))
		remaining = (len(self.channels) + bumps) % len(self.channels)
		selectedChannelIndex = self.channels.index(self.selectedChannel)

		if selectedChannelIndex + remaining > len(self.channels) - 1:
			bumpTo = selectedChannelIndex - len(self.channels) + remaining

		elif selectedChannelIndex + remaining < 0:
			bumpTo = len(self.channels) + selectedChannelIndex + remaining

		else:
			bumpTo = selectedChannelIndex + remaining

		print("bumps " + str(bumps) + ", bumping to: " + str(bumpTo))
		self.playChannel(self.channels[bumpTo])

	# Takes the parameter (int) and switches to that channel
	def set(self, channelNumber):
		if config.on == False:
			print("Can't switch channel when radio is off!")
			return

		self.selectedChannel = channelNumber

		config.player.stop()
		bestBitrateMatch = self.getBestBitRateMatch(self.selectedChannel["streams"])
		print("Playing channel with a bitrate of " + str(self.selectedChannel["streams"][bestBitrateMatch]["bitrate"]) + "kbps")
		config.player = vlc.MediaPlayer(self.selectedChannel["streams"][bestBitrateMatch]["url"])
		config.player.play()

		print("Channel " + str(self.selectedChannel) + " (" + self.selectedChannel["name"] + ")")
		
		display.notification(self.selectedChannel["name"])

	def getBestBitRateMatch(self, streams):
		bestMatchIndex = 0
		bestMatchBitrate = streams[0]["bitrate"]
		for i in range(len(streams)):
			if min(streams[i]["bitrate"] - config.quality, streams[bestMatchIndex]["bitrate"]) - config.quality != bestMatchBitrate:
				# print(str(i) + " (" + str(streams[i]["bitrate"]) + ") had a better matching bitrate than " + str(bestMatchIndex) + " (" + str(bestMatchBitrate) + ")")
				bestMatchBitrate = streams[i]["bitrate"]
				bestMatchIndex = i
		
		return bestMatchIndex

config.radio = Radio()