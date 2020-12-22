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
import os

_ = config.nno.gettext

from display.display import Display
from controls.registration import Registration
from helpers import helpers


class Radio():
	def __init__(self):
		self.registration = Registration(self)

		self.on = False
		self.channels = []
		self.instance = vlc.Instance()
		self.log = vlc.Log()
		self.player = self.instance.media_player_new()
		self.events = self.player.event_manager()
		self.media = self.instance.media_new("")
		self.selectedChannel = None
		# There is a delay before the browsed to channel is played. This variable holds the
		# "hovered" channel.
		self.hoveredChannel = None
		self.lastPowerState = None
		self.volume = int(os.environ["mnm_volume"])
		self.setVolume(self.volume)
		self.turnOnTime = None

		# A variable to hold the buffer timer.
		# Removes buffer from the state if there hasn't been sent another buffer event
		# since the timer started.
		self.bufferTimer = None

		# What the state was previous to buffering
		self.preBufferState = None

		# Is set when fetching channels. If it fails, we assume the server is down.
		self.serverUp = True

		# Bitrates
		# Put an int in the bitrate variable, and the stream closest to that bitrate will be used.
		# 32 kbps - Poor audio quality
		# 48 kbps - A reasonable lower end rate for longer speech-only podcasts
		# 64 kbps - A common bitrate for speech podcasts.
		# 128 kbps - Common standard for musical and high quality podcasts.
		# 320 kbps - Very high quality - almost indistinguishable from a CD.
		self.bitrate = int(os.environ["mnm_bitrate"])

		# Is set if the radio is updating (Dictionary)
		self.updating = None

		# String
		# Is set if there is a global error (ie. not related to channels)
		self.error = None

		# String
		# Is set if there is an error on the channel
		# Ie. if we couldn't open the channel
		self.channelError = None

		# State of radio (Dictionary)
		# { code: "buffering" || "ended" || "opening" || "paused" || "playing" || "stopped", text: "text description" }
		self.state = {
			"code": "starting",
			"text": _("Starting")
		}

		# When the user started listening. For analytics purposes.
		self.startedListeningTime = None

		self.saveListeningHistory = helpers.castToBool(os.environ["mnm_saveListeningHistory"])
		self.shouldSendState = helpers.castToBool(os.environ["mnm_sendState"])

		# Listen for VLC events
		self.events.event_attach(vlc.EventType.MediaPlayerOpening, self.openingEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerBuffering, self.bufferingEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerPlaying, self.playingEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerPaused, self.pausedEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerStopped, self.stoppedEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerEndReached, self.endReachedEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerEncounteredError, self.errorEvent)

		self.startStreamMonitor()

		# Start with channels from DB
		db = TinyDB('./db/db.json')
		radioTable = db.table("Radio_mnm")
		radio = radioTable.get(doc_id=1)

		channels = radio["channels"]
		if channels:
			self.channels = channels

		self.delayedBumpTimer = None

	def errorEvent(self, event = None):
		logger.error("errorEvent:, " + str(event))

	def endReachedEvent(self, event = None):
		logger.error("The player reacher the end... Weird... Did you lose the internet connection? Trying to restart the stream.")
		self.state = {
			"code": "endReached",
			"text": _("Stopped sending")
		}
		
		# Try to start stream again if it's "ended".
		time.sleep(1)
		self.player.play()

	def stoppedEvent(self, event = None):
		logger.debug("Stopped")
		self.state = {
			"code": "stopped",
			"text": _("Stopped playing")
		}

	def pausedEvent(self, event = None):
		logger.debug("Paused")
		self.state = {
			"code": "paused",
			"text": _("Paused playing")
		}

	def playingEvent(self, event = None):
		logger.debug("Playing")
		self.state = {
			"code": "playing",
			"text": _("Playing")
		}

	def openingEvent(self, event = None):
		logger.debug("Opening")
		self.state = {
			"code": "opening",
			"text": _("Opening channel")
		}

	def bufferingEvent(self, event = None):
		# The buffering event is sent very often while buffering, so let's limit setting state to once
		if self.state["code"] != "buffering":
			logger.debug("Buffering")
			
			self.preBufferState = self.state

			self.state = {
				"code": "buffering",
				"text": _("Buffering...")
			}
		
		# Cancel timer for setting state back from "buffering" if it's been set
		if self.bufferTimer:
			self.bufferTimer.cancel()

		# Start a timer to replace the "buffering" state with the state from before it was set to buffering
		self.bufferTimer = threading.Timer(0.2, self.setPreBufferState) 
		self.bufferTimer.start()

	def setPreBufferState(self):
		if self.preBufferState["code"] == "playing":
			self.playingEvent()
		elif self.preBufferState["code"] == "opening":
			self.openingEvent()
		else:
			logger.error("We don't support setting state to the registered preBufferState (" + self.preBufferState["code"] + ")")

		self.state = self.preBufferState

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
			t = threading.Thread(target=self.asyncFetchChannels, name='Fetching channels')
			# Daemonize it so we don't have to manually kill the thread
			t.daemon = True
			t.start()

	def asyncFetchChannels(self):
		db = TinyDB('./db/db.json')
		radioTable = db.table("Radio_mnm")
		radio = radioTable.get(doc_id=1)

		try:
			# Define status_code here, as if the request fails, we go straight
			# to the exception block, which evaluates status_code
			status_code = None

			headers = { "apiKey": radio["apiKey"] }
			response = requests.get(config.apiServer + "/radio/api/1/channels?homeId=" + radio["homeId"], headers=headers, verify=config.verifyCertificate, timeout=3)
			status_code = response.status_code
			response = response.json()
			
			if status_code == 200:
				logger.debug("Successfully fetched channels (" + str(status_code) + ")")
				self.channels = response["channels"]

				# Add channels to the database for use in case the server goes down
				radioTable.update({ "channels": self.channels }, doc_ids=[1])
				
				self.serverUp = True
			else:
				logger.error("Failed to fetch channels with HTTP error code: " + str(status_code))
		
		# Handle exceptions from failed requests
		except requests.exceptions.ConnectionError as exception:
			logger.error("Got a connection error while fetching channels:")
			logger.error(exception)

			self.display.notification(_("Failed to get\n\rchannels!"))
			time.sleep(2)

			# If status_code is not set, the request failed before returning
			if not status_code:
				logger.debug("Got no channels from the server (most likely a timeout). Is the server up?")
				self.serverUp = False
			elif status_code == 410:
				self.display.notification(_("This radio was\n\runregistered!"))
				time.sleep(3)
				self.display.notification(_("Resetting radio\n\rin three seconds"))
				self.registration.reset()
				return

			self.display.notification(_("No channels\n\ravailable!") + " (" + str(status_code) + ")")

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
		
		self.hoveredChannel = self.getHoveredChannelByOffset(bumps)

		if self.delayedBumpTimer:
			self.delayedBumpTimer.cancel()

		self.display.notification(self.hoveredChannel["name"], 2)
		self.delayedBumpTimer = threading.Timer(2, self.playChannel, args=[self.hoveredChannel])
		self.delayedBumpTimer.start()
		
	def getHoveredChannelByOffset(self, offset):
		# Number of channels to skip which remains after removing overflow.
		# (Overflow: if you are playing channel 3 of 10 and is instructed to skip 202 channels ahead,
		# you would end up on channel 205. The overflow is 200, and we should return channel 5 (3 + 2))
		remaining = (len(self.channels) + offset) % len(self.channels)
		if not self.hoveredChannel:
			self.hoveredChannel = self.selectedChannel
		hoveredChannelIndex = self.channels.index(self.hoveredChannel)
		bumpTo = 0

		if hoveredChannelIndex + remaining > len(self.channels) - 1:
			bumpTo = hoveredChannelIndex - len(self.channels) + remaining

		elif hoveredChannelIndex + remaining < 0:
			bumpTo = len(self.channels) + hoveredChannelIndex + remaining

		else:
			bumpTo = hoveredChannelIndex + remaining

		logger.debug("offset " + str(offset) + ", bumping to: " + str(bumpTo))
		return self.channels[bumpTo]

	def getChannelByOffset(self, offset):
		# Number of channels to skip which remains after removing overflow.
		# (Overflow: if you are playing channel 3 of 10 and is instructed to skip 202 channels ahead,
		# you would end up on channel 205. The overflow is 200, and we should return channel 5 (3 + 2))
		remaining = (len(self.channels) + offset) % len(self.channels)
		selectedChannelIndex = self.channels.index(self.selectedChannel)
		bumpTo = 0

		if selectedChannelIndex + remaining > len(self.channels) - 1:
			bumpTo = selectedChannelIndex - len(self.channels) + remaining

		elif selectedChannelIndex + remaining < 0:
			bumpTo = len(self.channels) + selectedChannelIndex + remaining

		else:
			bumpTo = selectedChannelIndex + remaining

		logger.debug("offset " + str(offset) + ", bumping to: " + str(bumpTo))
		return self.channels[bumpTo]

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
			if min(streams[i]["bitrate"] - self.bitrate, streams[bestMatchIndex]["bitrate"]) - self.bitrate != bestMatchBitrate:
				bestMatchBitrate = streams[i]["bitrate"]
				bestMatchIndex = i
		
		return bestMatchIndex

	# TODO: Make async, so we don't have to wait for request to be sent before switching channels
	def addToListeningHistory(self, startedListening, playedChannel, playingChannel = None):
		# Don't send requests if the server is (was) down
		if not self.serverUp:
			return False

		if not self.saveListeningHistory:
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

		try:
			response = requests.post(config.apiServer + "/radio/api/1/listeningHistory", data=data, verify=config.verifyCertificate, timeout=5)

			status_code = response.status_code
			response = response.json()
			
			if status_code == 200:
				logger.debug("Successfully posted listening history (" + str(status_code) + ")")
			else:
				logger.error("Couldn't post listening history: " + str(status_code))
		
		except requests.exceptions.ConnectionError as exception:
			logger.error("Got a connection error while adding to listening history:")
			logger.error(exception)

	def handleSendState(self, state):
		# Don't send requests if the server is (was) down
		if not self.serverUp:
			return False

		if not self.shouldSendState:
			return False

		# Quick and dirty way to make async
		# TODO: Revisit this
		threading.Timer(0, lambda: self.sendState(state)).start()

	def sendState(self, state):
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

		try:
			response = requests.post(config.apiServer + "/radio/api/1/state", data=data, verify=config.verifyCertificate, timeout=5)

			status_code = response.status_code
			response = response.json()
			
			if status_code == 200:
				logger.debug("Successfully posted state " + state + " (" + str(status_code) + ")")
			else:
				logger.error("Couldn't post state: " + str(status_code))
		
		except requests.exceptions.ConnectionError as exception:
			logger.error("Got a connection error while sending state " + state + ":")
			logger.error(exception)

	def handleError(self, error):
		if "VLC is unable to open the MRL" in error:
			print("Can't open channel")
			self.channelError = {
				"text": _("Can't open channel (MRL)"),
				"code": "cantOpenMrl"
			}

		# This error seems to resolve itself or just doesn't impact the radio
		elif "PulseAudio server connection failure: Connection refused" in error:
			# radio.error = {
			# 	"text": _("Can't output audio"),
			# 	"code": "pulseaudio"
			# }
			return False
			
		elif "unimplemented query (264) in control" in error:
			# TODO: Figure out what this is
			return False
	
	class StreamMonitor(threading.Thread):
		def __init__(self, parent):
			threading.Thread.__init__(self)
			self.parent = parent
			self.running = True
			self.stopCount = 0

			# When paused is set, the thread will run, when it's not set, the thread will wait
			self.pauseEvent = threading.Event()

		def run(self):
			while self.running:
				time.sleep(1)

				# If the radio is on and stopped on several checks, something is wrong
				if self.parent.on and self.parent.state["code"] == "stopped":
					self.stopCount = self.stopCount + 1

					if self.stopCount > 3:
						logger.error("Radio stopped for some reason. Lost Internet connection? Trying to restart...")
						self.parent.player.stop()
						self.parent.player.play()
						
						self.stopCount = 0
				else:
					self.stopCount = 0

				# Recover from channel errors
				if self.parent.channelError:
					logger.debug("Trying to recover from channel error: " + self.parent.channelError["code"])
					self.parent.channelError = None
					self.parent.player.stop()
					self.parent.player.play()

			if not self.running:
				return
		
		def stop(self):
			self.running = False
			print("Stopped the stream monitor loop")

	def startStreamMonitor(self):
		self.streamMonitor = self.StreamMonitor(self)
		self.streamMonitor.start()