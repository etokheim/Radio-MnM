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
import ctypes
import os

_ = config.nno.gettext

from display.display import Display
from controls.registration import Registration
from helpers import helpers

libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
vsnprintf = libc.vsnprintf

vsnprintf.restype = ctypes.c_int
vsnprintf.argtypes = (
    ctypes.c_char_p,
    ctypes.c_size_t,
    ctypes.c_char_p,
    ctypes.c_void_p,
)

# Your callback here
@vlc.CallbackDecorators.LogCb
def logCallback(data, level, ctx, fmt, args):
	# Skip if level is lower than error
	# TODO: Try to solve as many warnings as possible
	if level < 4:
		 return

	# Format given fmt/args pair
	BUF_LEN = 1024
	outBuf = ctypes.create_string_buffer(BUF_LEN)
	vsnprintf(outBuf, BUF_LEN, fmt, args)

	# Transform to ascii string
	log = outBuf.raw.decode('ascii').strip().strip('\x00')

	# Handle any errors
	if level > 3:
		shouldLog = config.radio.handleError(log)

		# If noisy error, then don't log it
		if not shouldLog:
			return

	# Output vlc logs to our log
	if level == 5:
		logger.critical(log)
	elif level == 4:
		logger.error(log)
	elif level == 3:
		logger.warning(log)
	elif level == 2:
		logger.info(log)


class Radio():
	def __init__(self):
		self.display = Display()
		self.registration = Registration()

		self.on = False
		self.channels = []
		self.instance = vlc.Instance()
		self.log = vlc.Log()
		self.player = self.instance.media_player_new()
		self.events = self.player.event_manager()
		self.media = self.instance.media_new("")
		self.selectedChannel = None
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
		self.sendState = helpers.castToBool(os.environ["mnm_sendState"])

		# Listen for VLC events
		self.instance.log_set(logCallback, None)
		self.events.event_attach(vlc.EventType.MediaPlayerOpening, self.openingEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerBuffering, self.bufferingEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerPlaying, self.playingEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerPaused, self.pausedEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerStopped, self.stoppedEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerEndReached, self.endReachedEvent)
		self.events.event_attach(vlc.EventType.MediaPlayerEncounteredError, self.errorEvent)

	def errorEvent(self, event = None):
		logger.error("errorEvent:, " + str(event))

	def endReachedEvent(self, event = None):
		logger.error("The player reacher the end... Weird... Did you lose the internet connection? Trying to restart the stream.")
		self.state = {
			"code": "endReached",
			"text": _("End reached")
		}
		
		# Try to start stream again if it's "ended".
		time.sleep(1)
		self.player.play()

	def stoppedEvent(self, event = None):
		logger.debug("Stopped")
		self.state = {
			"code": "stopped",
			"text": _("Stopped")
		}

	def pausedEvent(self, event = None):
		logger.debug("Paused")
		self.state = {
			"code": "paused",
			"text": _("Paused")
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
			"text": _("Opening...")
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
		db = TinyDB('./db/db.json')
		radioTable = db.table("Radio_mnm")
		radio = radioTable.get(doc_id=1)

		try:
			# Define status_code here, as if the request fails, we go straight
			# to the exception block, which evaluates status_code
			status_code = None

			headers = { "apiKey": radio["apiKey"] }
			response = requests.get(config.apiServer + "/radio/api/1/channels?homeId=" + radio["homeId"], headers=headers, verify=config.verifyCertificate, timeout=5)
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
				raise Exception(response, status_code)
		except Exception:
			self.display.notification(_("Failed to get\n\rchannels!"))
			time.sleep(2)
			logger.exception(Exception)

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

			# Recover by using channels from local db instead if we have them
			channels = radio["channels"]
			if channels:
				self.display.notification(_("Using local\n\rchannels instead"))
				time.sleep(1)
				self.channels = channels
			else:
				self.display.notification(_("Couldn't get\n\rchannels!") + " (" + str(status_code) + ")")
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

		response = requests.post(config.apiServer + "/radio/api/1/listeningHistory", data=data, verify=config.verifyCertificate, timeout=5)

		status_code = response.status_code
		response = response.json()
		
		if status_code == 200:
			logger.debug("Successfully posted listening history (" + str(status_code) + ")")
		else:
			logger.error("Couldn't post listening history: " + str(status_code))

	# TODO: Make async, so we don't have to wait for request to be sent before turning off
	def handleSendState(self, state):
		# Don't send requests if the server is (was) down
		if not self.serverUp:
			return False

		if not self.sendState:
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

		response = requests.post(config.apiServer + "/radio/api/1/state", data=data, verify=config.verifyCertificate, timeout=5)

		status_code = response.status_code
		response = response.json()
		
		if status_code == 200:
			logger.debug("Successfully posted state " + state + " (" + str(status_code) + ")")
		else:
			logger.error("Couldn't post state: " + str(status_code))

	def handleError(self, error):
		if "VLC is unable to open the MRL" in error:
			print("Can't open channel")
			config.radio.channelError = {
				"text": _("Can't open channel"),
				"code": 1
			}
		elif "PulseAudio server connection failure: Connection refused" in error:
			# Does this error fix itself?
			config.radio.error = _("Can't output audio")
		# elif "Network error" in error:
			# TODO: Handle temporary loss of internet access by repeatedly trying to restart the stream
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
				if config.radio.on and self.parent.state["code"] == "stopped":
					self.stopCount = self.stopCount + 1

					if self.stopCount > 3:
						logger.error("Radio stopped for some reason. Lost Internet connection? Trying to restart...")
						self.parent.player.stop()
						self.parent.player.play()
						
						self.stopCount = 0
				else:
					self.stopCount = 0

			if not self.running:
				return
		
		def stop(self):
			self.running = False
			print("Stopped the stream monitor loop")

	def startStreamMonitor(self):
		self.streamMonitor = self.StreamMonitor(self)
		self.streamMonitor.start()

config.radio = Radio()
config.radio.startStreamMonitor()