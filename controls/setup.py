# This is where initial setup and registration is handeled.
# Registration is done by registering with a server and receiving an api key in return.
# This key, and other information, is then stored in a simple database

from tinydb import TinyDB, Query
from display import display
import time
import requests
import os

class Registration():
	def __init__(self):
		print("Starting radio registration")

	def checkIfRegistered(self):
		isRegistered = requests.post("https://127.0.0.1:8000/api/1/isRegistered", data = {
			"code": self.response["code"]
		}, verify=False)
		isRegistered = isRegistered.json()
		return isRegistered

	def start(self):
		db = TinyDB('./db/db.json')
		Radio = Query()
		radioTable = db.table("Radio_mnm")
		radio = radioTable.search(Radio)
		
		print("radio")
		print(radio)

		if radio:
			print("This radio is already configured!")
			print(radio[0]["apiKey"])
		else:

			display.write("Acquiring codes")

			self.response = requests.get("https://127.0.0.1:8000/api/1/getRegisterCode", verify=False)
			self.response = self.response.json()

			display.write("Register radio:\n\r" + self.response["code"])

			# Check if the radio has been registered
			isRegistered = self.checkIfRegistered()
			while isRegistered["status"] == "pending":
				print(isRegistered)
				isRegistered = self.checkIfRegistered()
				time.sleep(1)
			
			if isRegistered["status"] == False:
				display.write("Code expired, \n\rfetching new one")
				time.sleep(1)
				self.start()
				return
			
			display.write("Registered! :D")
			print(isRegistered)

			radioTable.insert({
				"_id": isRegistered["radioId"],
				"registrationTime": int(round(time.time() * 1000)),
				"homeId": isRegistered["homeId"],
				"locationId": isRegistered["locationId"],
				"name": isRegistered["radio"]["name"],
				"apiKey": isRegistered["radio"]["apiKey"],
				"channels": []
			})

			print(radioTable)

registration = Registration()

def reset():
	display.write("Resetting radio")
	os.remove("./db/db.json")
	print("Removed database")
	registration.start()
	# set channels to undefined