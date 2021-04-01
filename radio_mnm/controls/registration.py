# This is where initial setup and registration is handeled.
# Registration is done by registering with a server and receiving an api key in return.
# This key, and other information, is then stored in a simple database

import logging
logger = logging.getLogger("Radio_mnm")
import time
import requests
import os
from tinydb import TinyDB, Query
from config.config import config
import gettext
import threading
import sys

_ = config["getLanguage"].gettext

class Registration():
	def __init__(self, radio):
		self.radio = radio
		logger.debug("Checking if radio is registered")
		self.tooWideCodeErrorCount = 0
		self.checkIfRegisteredLoop = None

	def checkIfRegistered(self):
		isRegistered = requests.post(config["apiServer"] + "/api/1/isRegistered", data = {
			"code": self.response["code"]
		}, verify=config["verifyCertificate"])
		isRegistered = isRegistered.json()
		return isRegistered

	def start(self):
		db = TinyDB('./db/db.json')
		radioTable = db.table("Radio_mnm")
		radio = radioTable.get(doc_id=1)
		
		if radio:
			logger.debug("Radio is registered.")
			
			# Update channels
			self.radio.loop.create_task(
				self.radio.fetchChannels()
			)
		else:
			logger.debug("Radio isn't registered! Starting registration.")

			self.response = requests.get(config["apiServer"] + "/api/1/getRegisterCode", verify=config["verifyCertificate"])
			self.response = self.response.json()

			# If the code doesn't fit on the screen, start over
			if len(self.response["code"]) > self.radio.display.displayWidth:
				self.tooWideCodeErrorCount = self.tooWideCodeErrorCount + 1
				self.start()
				return

			if self.tooWideCodeErrorCount >= 10:
				logger.error("Couldn't get a code that fit on the display")
				self.radio.display.notification(_("Too tiny display"))
				sys.exit(1)

			# Display the code on the display
			if self.radio.display.displayHeight == 1:
				self.radio.display.standardContent = self.response["code"]
			else:
				self.radio.display.standardContent = _("Register radio:") + "\n\r" + self.response["code"]
			
			# Start isRegisteredThread
			self.checkIfRegisteredLoop = self.CheckIfRegisteredLoop(self)
			self.checkIfRegisteredLoop.start()

	class CheckIfRegisteredLoop(threading.Thread):
		def __init__(self, parent):
			threading.Thread.__init__(self)

			self.name = "Check if registered loop"
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
				if not self.parent.radio.on:
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
				if self.parent.radio.display.displayHeight == 1:
					self.parent.radio.display.notification(_("Getting new code"))
				else:
					self.parent.radio.display.notification(_("Code expired, \n\rfetching new one"))
					
				# Give user time to read the message
				time.sleep(1)
				self.start()
				return
			
			self.parent.radio.display.notification(_("Registered! :D"))
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
			self.parent.radio.loop.create_task(
				self.parent.radio.fetchChannels()
			)
			
			# And finally start playing
			if len(self.parent.radio.channels) > 0:
				self.parent.radio.play()
		
		def stop(self):
			self.running = False
			logger.debug("Stopped the loop for checking if the radio is registered.")
	
	def reset(self):
		# Stop the checkIfRegisteredLoop if it's running. It's only running if the radio is in the
		# middle of registering.
		if self.checkIfRegisteredLoop:
			self.checkIfRegisteredLoop.stop()

		self.radio.display.notification(_("Resetting radio") + "\n****************")

		# Stop playing
		self.radio.stop()

		# TODO: Send request to delete itself
		
		time.sleep(2)
		os.remove("./db/db.json")
		logger.warning("Removed database")

		# Remove the old channels from memory
		self.radio.channels = []
		self.radio.media = self.radio.instance.media_new("")
		self.radio.selectedChannel = None
		
		self.start()
