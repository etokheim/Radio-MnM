import logging
logger = logging.getLogger("Radio_mnm")
from config.config import config
import os
import requests
from tinydb import TinyDB, Query
import sys
import time
import gettext
import socket
import subprocess
import threading
import asyncio

if os.name == "nt":
	os.add_dll_directory(r"C:\Program Files\VideoLAN\VLC")

import vlc

_ = config["getLanguage"].gettext

from controls.registration import Registration


class Radio():
	def __init__(self):
		self.registration = Registration(self)
		self.loop = asyncio.get_event_loop()

		self.events = {
			"unregister": [],
			"on": [],
			"off": [],
			"volume": [],
			"meta": [],
			"newChannel": [],
			"newState": []
		}

		self.on = False
		self.offContent = False
		self.channels = []
		self.instance = vlc.Instance()
		self.log = vlc.Log()
		self.player = self.instance.media_player_new()
		self.vlcEvents = self.player.event_manager()
		self.media = self.instance.media_new("")
		self.selectedChannel = None
		self.lastPowerState = None
		self.volume = config["audio"]["volume"]
		self.setVolume(self.volume)
		self.powerOnTime = None
		self.powerOffTime = int(round(time.time() * 1000))
		self.meta = {
			"whatsPlaying": None
		}

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
		self.bitrate = config["audio"]["bitrate"]

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

		self.saveListeningHistory = config["saveListeningHistory"]
		self.shouldSendState = config["sendState"]

		# Listen for VLC events
		self.vlcEvents.event_attach(vlc.EventType.MediaPlayerOpening, self.openingEvent)
		self.vlcEvents.event_attach(vlc.EventType.MediaPlayerBuffering, self.bufferingEvent)
		self.vlcEvents.event_attach(vlc.EventType.MediaPlayerPlaying, self.playingEvent)
		self.vlcEvents.event_attach(vlc.EventType.MediaPlayerPaused, self.pausedEvent)
		self.vlcEvents.event_attach(vlc.EventType.MediaPlayerStopped, self.stoppedEvent)
		self.vlcEvents.event_attach(vlc.EventType.MediaPlayerEndReached, self.endReachedEvent)
		self.vlcEvents.event_attach(vlc.EventType.MediaPlayerEncounteredError, self.errorEvent)

		self.streamMonitor = self.StreamMonitor(self)
		self.streamMonitor.start()

		# Start with channels from DB
		db = TinyDB('./db/db.json')
		radioTable = db.table("Radio_mnm")
		radio = radioTable.get(doc_id=1)

		channels = radio["channels"]
		if channels:
			self.channels = channels
		
		# Attach frontend
		if "frontend" in config:
			if config["frontend"] == "emulatedFrontend":
				import front_ends.emulatedFrontend
				self.frontend = front_ends.emulatedFrontend.EmulatedFrontend(self)
			
			if config["frontend"] == "characterDisplay":
				import front_ends.characterDisplay as characterDisplay
				self.frontend = characterDisplay.CharacterDisplay(self)

		else:
			raise Exception("Missing frontend. Please specify the frontend you want in the config.yml file.")

	# Loops through the callbacks parameter (array) and executes them
	def dispatch(self, callbacks, args = []):
		for callback in callbacks:
			if callback:
				if args:
					callback(*args)
				else:
					callback()

	def addEventListener(self, type, callback):
		if type == "unregister":
			self.events["unregister"].append(callback)
		elif type == "on":
			self.events["on"].append(callback)
		elif type == "off":
			self.events["off"].append(callback)
		elif type == "volume":
			self.events["volume"].append(callback)
		elif type == "meta":
			self.events["meta"].append(callback)
		elif type == "newChannel":
			self.events["newChannel"].append(callback)
		elif type == "newState":
			self.events["newState"].append(callback)
		else:
			raise Exception("Event type " + str(callback) + "is not supported.")

	def errorEvent(self, event = None):
		logger.error("errorEvent:, " + str(event))

	def endReachedEvent(self, event = None):
		logger.error("The player reacher the end... Weird... Did you lose the internet connection? Trying to restart the stream.")
		self.state = {
			"code": "endReached",
			"text": _("Stopped sending")
		}

		self.dispatch(self.events["newState"], args = [self.state])
		
		# Try to start stream again if it's "ended".
		time.sleep(1)
		self.player.play()

	def stoppedEvent(self, event = None):
		logger.debug("Stopped")
		self.state = {
			"code": "stopped",
			"text": _("Stopped playing")
		}

		self.dispatch(self.events["newState"], args = [self.state])

	def pausedEvent(self, event = None):
		logger.debug("Paused")
		self.state = {
			"code": "paused",
			"text": _("Paused playing")
		}

		self.dispatch(self.events["newState"], args = [self.state])

	def playingEvent(self, event = None):
		logger.debug("Playing")
		self.state = {
			"code": "playing",
			"text": _("Playing")
		}

		self.dispatch(self.events["newState"], args = [self.state])

	def openingEvent(self, event = None):
		logger.debug("Opening")
		self.state = {
			"code": "opening",
			"text": _("Opening channel")
		}

		self.dispatch(self.events["newState"], args = [self.state])

	def bufferingEvent(self, event = None):
		# The buffering event is sent very often while buffering, so let's limit setting state to once
		if self.state["code"] != "buffering":
			logger.debug("Buffering")
			
			self.preBufferState = self.state

			self.state = {
				"code": "buffering",
				"text": _("Buffering...")
			}

			self.dispatch(self.events["newState"], args = [self.state])
		
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
		self.dispatch(self.events["newState"], args = [self.state])

	def togglePower(self):
		if self.on:
			self.powerOff()
		else:
			self.powerOn()

	def powerOff(self):
		self.on = False
		self.powerOffTime = int(round(time.time() * 1000))
		self.stop()
		self.dispatch(self.events["off"])
		self.loop.create_task(self.sendState("suspended"))

	def powerOn(self):
		self.on = True
		self.powerOnTime = int(round(time.time() * 1000))

		# Start playing
		if not self.selectedChannel:
			self.selectedChannel = self.channels[0]
	
		self.dispatch(self.events["on"])
		self.play()

		# TODO: Maybe rename .start() methods that aren't threads, as it can be confusing.
		# Starts the registration if the radio isn't registered
		self.registration.start()

		if self.lastPowerState != "off":
			self.loop.create_task(self.sendState("noPower"))

		self.loop.create_task(self.sendState("on"))

		# if len(self.channels) > 0:
		# 	self.play()

	def playChannel(self, channel):
		# Channel should always be valid, so this clause shouldn't trigger, unless there is a bug.
		if not channel:
			logger.error("Channel parameter is not a valid channel. Can't start player.")
			return
		elif channel == self.selectedChannel and self.state["code"] == "playing":
			logger.debug("Switching to the same channel that was already playing. Skipping restart.")
			return

		# Before we update the selected channel, store the last played one
		playedChannel = self.selectedChannel

		self.selectedChannel = channel
		self.dispatch(self.events["newChannel"])
		bestBitrateMatch = self.getBestBitRateMatch(channel["streams"])
		logger.debug("Playing " + channel["name"] + " with a bitrate of " + str(channel["streams"][bestBitrateMatch]["bitrate"]) + "kbps")

		self.player.stop()
		url = channel["streams"][bestBitrateMatch]["url"]
		self.media = self.instance.media_new(url)
		self.player.set_media(self.media)
		self.player.play()
		
		# Add the previous listen to the history
		self.loop.create_task(
			self.addToListeningHistory(self.startedListeningTime, playedChannel, self.selectedChannel)
		)

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
			self.loop.create_task(
				self.addToListeningHistory(self.startedListeningTime, self.selectedChannel)
			)

	async def fetchChannels(self):
		db = TinyDB('./db/db.json')
		radioTable = db.table("Radio_mnm")
		radio = radioTable.get(doc_id=1)

		try:
			# Define status_code here, as if the request fails, we go straight
			# to the exception block, which evaluates status_code
			status_code = None

			headers = { "apiKey": radio["apiKey"] }
			response = requests.get(config["apiServer"] + "/radio/api/1/channels?homeId=" + radio["homeId"], headers=headers, verify=config["verifyCertificate"], timeout=3)
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

			self.display.notification(_("Failed to get\n\rnew channels!"))

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
		
		self.playChannel(self.getChannelByOffset(bumps))
	
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
		# Don't allow volumes less than 0 or more than 100
		if volume < 0:
			volume = 0
		elif volume > 100:
			volume = 100

		self.volume = volume
		self.dispatch(self.events["volume"], { "volume": volume })

		# Setting the volume actually takes a sec, so we'll execute it asyncrhonously
		self.loop.create_task(
			self.communicateNewVolumeLevel(volume)
		)
	
	async def communicateNewVolumeLevel(self, volume):
		try:
			if "emulatedVolume" in config["audio"] and config["audio"]["emulatedVolume"]:
				pass
			else:
				output = subprocess.check_output(["amixer", "-D", "pulse", "sset", "Master", str(volume) + "%"])
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

	async def addToListeningHistory(self, startedListening, playedChannel, playingChannel = None):
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
			response = requests.post(config["apiServer"] + "/radio/api/1/listeningHistory", data=data, verify=config["verifyCertificate"], timeout=5)

			status_code = response.status_code
			response = response.json()
			
			if status_code == 200:
				logger.debug("Successfully posted listening history (" + str(status_code) + ")")
			else:
				logger.error("Couldn't post listening history: " + str(status_code))
		
		except requests.exceptions.ConnectionError as exception:
			logger.error("Got a connection error while adding to listening history:")
			logger.error(exception)

	async def sendState(self, state):
		# Don't send requests if the server is (was) down
		if not self.serverUp:
			return False

		if not self.shouldSendState:
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

		try:
			response = requests.post(config["apiServer"] + "/radio/api/1/state", data=data, verify=config["verifyCertificate"], timeout=5)

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
				time.sleep(0.5)

				whatsPlaying = self.parent.media.get_meta(12)
				if self.parent.meta["whatsPlaying"] != whatsPlaying:
					self.parent.meta["whatsPlaying"] = whatsPlaying
					self.parent.dispatch(self.parent.events["meta"], self.parent.meta)


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

		