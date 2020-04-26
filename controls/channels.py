import logging
logger = logging.getLogger("Radio_mnm")
import vlc
import requests
from tinydb import TinyDB, Query
import sys
import time

from display.display import display
from config import config
from controls import setup

class Radio():
	def __init__(self):
		self.channels = []
		self.instance = vlc.Instance()
		self.player = self.instance.media_player_new()
		self.media = self.instance.media_new("")
		self.selectedChannel = None

	def playChannel(self, channel):
		self.selectedChannel = channel
		bestBitrateMatch = self.getBestBitRateMatch(channel["streams"])
		logger.info("Playing channel with a bitrate of " + str(channel["streams"][bestBitrateMatch]["bitrate"]) + "kbps")

		self.player.stop()
		url = channel["streams"][bestBitrateMatch]["url"]
		self.media = self.instance.media_new(url)
		self.player.set_media(self.media)
		self.player.play()

	def play(self):
		self.playChannel(self.selectedChannel)

	def stop(self):
		self.player.stop()

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
			
			if status_code == 200:
				logger.debug("Successfully fetched channels (" + str(status_code) + ")")
				self.channels = response["channels"]

				# Add channels to the database for use in case the server goes down
				radioTable.update({ "channels": self.channels }, doc_ids=[1])
			else:
				logger.error("Failed to fetch channels with HTTP error code: " + str(status_code))
				raise Exception(response, status_code)
		except Exception:
			display.notificationMessage("Failed to get\n\rchannels!")
			time.sleep(2)
			logger.exception(Exception)
			
			if status_code == 410:
				display.notificationMessage("This radio was\n\runregistered!")
				time.sleep(3)
				display.notificationMessage("Resetting radio\n\rin three seconds")
				setup.reset()
				return

			# Recover by using channels from local db instead if we have them
			channels = radio["channels"]
			if channels:
				display.notificationMessage("Using local\n\rchannels instead")
				time.sleep(1)
				self.channels = channels
			else:
				display.notificationMessage("Couldn't get\n\rchannels! (" + str(status_code) + ")")
				logger.error("------------ EXITED ------------")
				time.sleep(1)
				# Exit with code "112, Host is down"
				sys.exit(112)

		# TODO: Only set selectedChannel if it's not set
		if not self.selectedChannel:
			self.selectedChannel = self.channels[0]

		# self.playChannel(self.selectedChannel)

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

		logger.debug("bumps " + str(bumps) + ", bumping to: " + str(bumpTo))
		self.playChannel(self.channels[bumpTo])

	def getBestBitRateMatch(self, streams):
		bestMatchIndex = 0
		bestMatchBitrate = streams[0]["bitrate"]

		for i in range(len(streams)):
			if min(streams[i]["bitrate"] - config.quality, streams[bestMatchIndex]["bitrate"]) - config.quality != bestMatchBitrate:
				bestMatchBitrate = streams[i]["bitrate"]
				bestMatchIndex = i
		
		return bestMatchIndex

config.radio = Radio()