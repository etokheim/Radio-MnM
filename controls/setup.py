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

_ = config.nno.gettext

from display.display import display
from config import config
from controls import channels

class Registration():
	def __init__(self):
		logger.info("Starting radio registration")

	def checkIfRegistered(self):
		isRegistered = requests.post(config.apiServer + "/api/1/isRegistered", data = {
			"code": self.response["code"]
		}, verify=config.verifyCertificate)
		isRegistered = isRegistered.json()
		return isRegistered

	def start(self):
		db = TinyDB('./db/db.json')
		Radio = Query()
		radioTable = db.table("Radio_mnm")
		radio = radioTable.search(Radio)

		if radio:
			logger.debug("This radio is already configured!")
		else:
			display.notification(_("Acquiring codes"))

			self.response = requests.get(config.apiServer + "/api/1/getRegisterCode", verify=config.verifyCertificate)
			self.response = self.response.json()

			# Display the code on the display, and set the display duration to a very long time
			display.notification(_("Register radio:") + "\n\r" + self.response["code"], 100000)

			# Check if the radio has been registered
			isRegistered = self.checkIfRegistered()
			while isRegistered["status"] == "pending":
				logger.debug(isRegistered)
				isRegistered = self.checkIfRegistered()
				time.sleep(1)
			
			if isRegistered["status"] == False:
				display.notification(_("Code expired, \n\rfetching new one"))
				time.sleep(1)
				self.start()
				return
			
			display.notification(_("Registered! :D"))
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
			
			# Then fetch channels again, so we don't use the old ones until the user restarts
			# the radio.
			config.radio.fetchChannels()

registration = Registration()

def reset():
	display.notification(_("Resetting radio") + "\n****************")

	# Stop playing
	config.radio.stop()

	# TODO: Send request to delete itself
	
	time.sleep(2)
	os.remove("./db/db.json")
	logger.warning("Removed database")

	# Remove the old channels from memory
	config.radio.channels = []
	
	registration.start()