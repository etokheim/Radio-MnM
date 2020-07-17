import logging
logger = logging.getLogger("Radio_mnm")
from config import config
import vlc
import requests
from tinydb import TinyDB, Query
import sys
import time
import gettext
import socket
import subprocess
import threading

_ = config.nno.gettext

from display.display import display
from controls import setup

class Radio():
	def __init__(self):
		self.channels = []
		self.instance = vlc.Instance()
		self.player = self.instance.media_player_new()
		self.media = self.instance.media_new("")
		self.selectedChannel = None
		self.lastPowerState = None
		self.volume = config.volume
		self.setVolume(self.volume)

		# Get state of player (class Vlc.state)
		# Buffering || Ended || Error || NothingSpecial || Opening || Paused || Playing || Stopped
		self.getState = self.player.get_state

		# When the user started listening. For analytics purposes.
		self.startedListeningTime = None

	def playChannel(self, channel):
		# Channel should always be valid, so this clause shouldn't trigger, unless there is a bug.
		if not channel:
			logger.error("Channel parameter is not a valid channel. Can't start player.")
			return

		# Before we update the selected channel, store the last played one
		playedChannel = self.selectedChannel

		self.selectedChannel = channel
		bestBitrateMatch = self.getBestBitRateMatch(channel["streams"])
		logger.debug("Playing " + channel["name"] + " with a bitrate of " + str(channel["streams"][bestBitrateMatch]["bitrate"]) + "kbps")

		self.player.stop()
		url = channel["streams"][bestBitrateMatch]["url"]
		self.media = self.instance.media_new(url)
		self.player.set_media(self.media)
		self.player.play()
		
		# Add the previous listen to the history
		self.addToListeningHistory(self.startedListeningTime, playedChannel, self.selectedChannel)

		# Note when we started listening
		self.startedListeningTime = int(round(time.time() * 1000))

	def play(self):
		self.playChannel(self.selectedChannel)

	def stop(self):
		# Only stop the radio if something is playing. Otherwise we will get an error
		# if the user turns of the radio when the radio isn't registered
		if self.selectedChannel:
			self.media = self.instance.media_new("")
			self.player.stop()
			self.addToListeningHistory(self.startedListeningTime, self.selectedChannel)

	def fetchChannels(self):
		db = TinyDB('./db/db.json')
		radioTable = db.table("Radio_mnm")
		radio = radioTable.get(doc_id=1)

		try:
			headers = { "apiKey": radio["apiKey"] }
			response = requests.get(config.apiServer + "/radio/api/1/channels?homeId=" + radio["homeId"], headers=headers, verify=config.verifyCertificate)
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
			display.notification(_("Failed to get\n\rchannels!"))
			time.sleep(2)
			logger.exception(Exception)
			
			if status_code == 410:
				display.notification(_("This radio was\n\runregistered!"))
				time.sleep(3)
				display.notification(_("Resetting radio\n\rin three seconds"))
				setup.registration.reset()
				return

			# Recover by using channels from local db instead if we have them
			channels = radio["channels"]
			if channels:
				display.notification(_("Using local\n\rchannels instead"))
				time.sleep(1)
				self.channels = channels
			else:
				display.notification(_("Couldn't get\n\rchannels!") + " (" + str(status_code) + ")")
				logger.error("------------ EXITED ------------")
				time.sleep(1)
				# Exit with code "112, Host is down"
				sys.exit(112)

		# Only sets selectedChannel if it's not set and the radio has channels.
		# If not, keep the None value
		if not self.selectedChannel and len(self.channels) > 0:
			self.selectedChannel = self.channels[0]

		# self.playChannel(self.selectedChannel)

	# Bumps the channel n times. Loops around if bumping past the last channel.
	def bump(self, bumps = 1):
		if not self.channels:
			logger.debug("Can't bump channel when there are none available.")
			return

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

	def setVolume(self, volume):
		try:
			subprocess.call(["amixer", "-D", "pulse", "sset", "Master", str(volume) + "%"])
			return True
		
		except ValueError:
			pass


	def getBestBitRateMatch(self, streams):
		bestMatchIndex = 0
		bestMatchBitrate = streams[0]["bitrate"]

		for i in range(len(streams)):
			if min(streams[i]["bitrate"] - config.bitrate, streams[bestMatchIndex]["bitrate"]) - config.bitrate != bestMatchBitrate:
				bestMatchBitrate = streams[i]["bitrate"]
				bestMatchIndex = i
		
		return bestMatchIndex

	def addToListeningHistory(self, startedListening, playedChannel, playingChannel = None):
		if not config.saveListeningHistory:
			return False

		db = TinyDB('./db/db.json')
		radioTable = db.table("Radio_mnm")
		radio = radioTable.get(doc_id=1)
		
		# PlayingChannel can be None. Ie. if we are stopping the player.
		if playingChannel == None:
			playingChannel = {
				"_id": None
			}

		data = {
			"homeId": radio["homeId"],
			"apiKey": radio["apiKey"],
			"playedChannelId": playedChannel["_id"],
			"playedChannelStartTime": startedListening,
			"playedChannelEndTime": int(round(time.time() * 1000)), # Now in UNIX time
			"playingChannelId": playingChannel["_id"]
		}

		response = requests.post(config.apiServer + "/radio/api/1/listeningHistory", data=data, verify=config.verifyCertificate)

		status_code = response.status_code
		response = response.json()
		
		if status_code == 200:
			logger.debug("Successfully posted listening history (" + str(status_code) + ")")
		else:
			logger.error("Couldn't post listening history: " + str(status_code))

	def sendState(self, state):
		if not config.sendState:
			return False
		
		db = TinyDB('./db/db.json')
		radioTable = db.table("Radio_mnm")
		radio = radioTable.get(doc_id=1)

		# Stop if radio doesn't exist (if device is registered)
		if not radio:
			logger.debug("Can't post radio state to the API when the radio isn't registered.")
			return False

		data = {
			"homeId": radio["homeId"],
			"apiKey": radio["apiKey"],
			"state": state,
			"ip": socket.gethostbyname(socket.gethostname())
		}

		response = requests.post(config.apiServer + "/radio/api/1/state", data=data, verify=config.verifyCertificate)

		status_code = response.status_code
		response = response.json()
		
		if status_code == 200:
			logger.debug("Successfully posted state " + state + " (" + str(status_code) + ")")
		else:
			logger.error("Couldn't post state: " + str(status_code))

	def getStateText(self):
		# TODO: Find a better way to do this.
		# state's type is <class 'vlc.State'>
		# I'd rather not compare strings if I don't have to.
		state = self.player.get_state()
		strState = str(state)
		if strState == "State.Playing":
			return "Playing"
			
		elif strState == "State.Buffering":
			return "Buffering"

		elif strState == "State.Ended":
			return "Ended"

		elif strState == "State.Error":
			return "Error"

		elif strState == "State.NothingSpecial":
			return "NothingSpecial"

		elif strState == "State.Opening":
			return "Opening"

		elif strState == "State.Paused":
			return "Paused"

		elif strState == "State.Stopped":
			return "Stopped"

		else:
			return strState
	

config.radio = Radio()