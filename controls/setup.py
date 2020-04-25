# This is where initial setup and registration is handeled.
# Registration is done by registering with a server and receiving an api key in return.
# This key, and other information, is then stored in a simple database

import time
import requests
import os
import logging
from tinydb import TinyDB, Query

from display.display import display
from config import config

class Registration():
	def __init__(self):
		logging.info("Starting radio registration")

	def checkIfRegistered(self):
		isRegistered = requests.post(config.apiServer + "/api/1/isRegistered", data = {
			"code": self.response["code"]
		}, verify=False)
		isRegistered = isRegistered.json()
		return isRegistered

	def start(self):
		db = TinyDB('./db/db.json')
		Radio = Query()
		radioTable = db.table("Radio_mnm")
		radio = radioTable.search(Radio)

		if radio:
			logging.debug("This radio is already configured!")
		else:

			display.notificationMessage("Acquiring codes")

			self.response = requests.get(config.apiServer + "/api/1/getRegisterCode", verify=False)
			self.response = self.response.json()

			display.notificationMessage("Register radio:\n\r" + self.response["code"])

			# Check if the radio has been registered
			isRegistered = self.checkIfRegistered()
			while isRegistered["status"] == "pending":
				logging.debug(isRegistered)
				isRegistered = self.checkIfRegistered()
				time.sleep(1)
			
			if isRegistered["status"] == False:
				display.notificationMessage("Code expired, \n\rfetching new one")
				time.sleep(1)
				self.start()
				return
			
			display.notificationMessage("Registered! :D")
			logging.info("Device successfully registered!")

			radioTable.insert({
				"_id": isRegistered["radioId"],
				"registrationTime": int(round(time.time() * 1000)),
				"homeId": isRegistered["homeId"],
				"locationId": isRegistered["locationId"],
				"name": isRegistered["radio"]["name"],
				"apiKey": isRegistered["radio"]["apiKey"],
				"channels": []
			})

registration = Registration()

def reset():
	display.notificationMessage("Resetting radio\n****************")
	# TODO: Send request to delete itself
	time.sleep(2)
	os.remove("./db/db.json")
	logging.warning("Removed database")
	registration.start()
	# set channels to undefined