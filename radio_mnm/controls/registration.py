# This is where initial setup and registration is handeled.
# Registration is done by registering with a server and receiving an api key in return.
# This key, and other information, is then stored in a simple database

import logging
logger = logging.getLogger("Radio_mnm")
import time
import requests
import os
from tinydb import TinyDB, Query
from config import config
import gettext
import threading
import sys

_ = config.nno.gettext

from config import config
from controls import radio

class Registration():
	def __init__(self):
		logger.debug("Checking if radio is registered")
		self.tooWideCodeErrorCount = 0
		self.checkIfRegisteredLoop = None

	def checkIfRegistered(self):
		isRegistered = requests.post(config.apiServer + "/api/1/isRegistered", data = {
			"code": self.response["code"]
		}, verify=config.verifyCertificate)
		isRegistered = isRegistered.json()
		return isRegistered

	def start(self):
		db = TinyDB('./db/db.json')
		radioTable = db.table("Radio_mnm")
		radio = radioTable.get(doc_id=1)
		
		if radio:
			logger.debug("Radio is registered.")
			
			# Update channels
			config.radio.fetchChannels()
		else:
			logger.debug("Radio isn't registered! Starting registration.")

			self.response = requests.get(config.apiServer + "/api/1/getRegisterCode", verify=config.verifyCertificate)
			self.response = self.response.json()

			# If the code doesn't fit on the screen, start over
			if len(self.response["code"]) > config.displayWidth:
				self.tooWideCodeErrorCount = self.tooWideCodeErrorCount + 1
				self.start()
				return

			if self.tooWideCodeErrorCount >= 10:
				logger.error("Couldn't get a code that fit on the display")
				config.radio.display.notification(_("Too tiny display"))
				sys.exit(1)

			# Display the code on the display, and set the display duration to a very long time
			if config.displayHeight == 1:
				config.radio.display.standardContent = self.response["code"]
			else:
				config.radio.display.standardContent = _("Register radio:") + "\n\r" + self.response["code"]
			
			# Start isRegisteredThread
			self.checkIfRegisteredLoop = self.CheckIfRegisteredLoop(self)
			self.checkIfRegisteredLoop.start()

	class CheckIfRegisteredLoop(threading.Thread):
		def __init__(self, parent):
			threading.Thread.__init__(self)

			self.parent = parent
			self.running = True

			# When paused is set, the thread will run, when it's not set, the thread will wait
			self.pauseEvent = threading.Event()

		def run(self):
			# Check if the radio has been registered
			isRegistered = self.parent.checkIfRegistered()
			while isRegistered["status"] == "pending" and self.running:
				time.sleep(1)
				logger.debug(isRegistered)
				isRegistered = self.parent.checkIfRegistered()

				# If the radio is turned off, stop checking if it's been registered.
				if not config.radio.on:
					self.stop()
					return

			if not self.running:
				return

			# When the radio is registered, stop the loop
			self.stop()

			# Finish up registration			
			db = TinyDB('./db/db.json')
			radioTable = db.table("Radio_mnm")

			if isRegistered["status"] == False:
				if config.displayHeight == 1:
					config.radio.display.notification(_("Getting new code"))
				else:
					config.radio.display.notification(_("Code expired, \n\rfetching new one"))
					
				# Give user time to read the message
				time.sleep(1)
				self.start()
				return
			
			config.radio.display.notification(_("Registered! :D"))
			logger.info("Device successfully registered!")

			radioTable.insert({
				"_id": isRegistered["radioId"],
				"registrationTime": int(round(time.time() * 1000)),
				"homeId": isRegistered["homeId"],
				"locationId": isRegistered["locationId"],
				"name": isRegistered["radio"]["name"],
				"apiKey": isRegistered["radio"]["apiKey"],
				"channels": []
			})
			
			# Then fetch channels
			config.radio.fetchChannels()
			
			# And finally start playing
			if len(config.radio.channels) > 0:
				config.radio.play()
		
		def stop(self):
			self.running = False
			logger.debug("Stopped the loop for checking if the radio is registered.")
	
	def reset(self):
		# Stop the checkIfRegisteredLoop if it's running. It's only running if the radio is in the
		# middle of registering.
		if self.checkIfRegisteredLoop:
			self.checkIfRegisteredLoop.stop()

		config.radio.display.notification(_("Resetting radio") + "\n****************")

		# Stop playing
		config.radio.stop()

		# TODO: Send request to delete itself
		
		time.sleep(2)
		os.remove("./db/db.json")
		logger.warning("Removed database")

		# Remove the old channels from memory
		config.radio.channels = []
		config.radio.media = config.radio.instance.media_new("")
		config.radio.selectedChannel = None
		
		self.start()
