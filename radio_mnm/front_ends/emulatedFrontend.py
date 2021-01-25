from config.config import config
import threading
import time
import logging
import tkinter as tk
import os
import ctypes
logger = logging.getLogger("Radio_mnm")
_ = config["getLanguage"].gettext

class EmulatedFrontend(threading.Thread):
	def __init__(self, radio):
		threading.Thread.__init__(self)
		self.radio = radio

		self.root = None
		self.start()

		# Attach components
		if "components" in config:
			if "emulatedNavigationButton" in config["components"]:
				if config["components"]["emulatedNavigationButton"]:
					import handlers.emulatedButton as emulatedButton
					self.emulatedNavigationButton = emulatedButton.Button(self.root, "Navigation Button")

					# Listen to the button
					self.emulatedNavigationButton.addEventListener("click", lambda: self.radio.bump())
					self.emulatedNavigationButton.addEventListener("longPress", lambda: self.radio.bump(-1))
					self.emulatedNavigationButton.addEventListener("veryLongPress", lambda: print("Start reset sequence"))
			
			if "emulatedPowerButton" in config["components"]:
				if config["components"]["emulatedPowerButton"]:
					import handlers.emulatedButton as emulatedButton
					self.emulatedPowerButton = emulatedButton.Button(self.root, "Power Button")

					self.emulatedPowerButton.addEventListener("click", radio.togglePower)
			
		# Add event listeners
		radio.addEventListener("on", self.handleOn)
		radio.addEventListener("off", self.handleOff)

		# Handle high DPI displays
		if os.name == "nt":
			import ctypes
			ctypes.windll.shcore.SetProcessDpiAwareness(1)

	def run(self):
		self.root = tk.Tk()
		root = self.root
		screenWidth = root.winfo_screenwidth()
		screenHeight = root.winfo_screenheight()
		root.wm_title("Radio M&M")
		root.protocol("WM_DELETE_WINDOW", self.closeWindow)
		windowWidth = 600
		windowHeight = 400
		root.geometry(str(windowWidth) + "x" + str(windowHeight) + "+" + str(round(screenWidth/2)) + "+" + str(round(screenHeight/2)))

		self.infoText = tk.StringVar()
		self.label = tk.Label(root, textvariable=self.infoText)
		self.label.pack()
		self.writeInfo()

		self.root.mainloop()

	def closeWindow(self):
		print("Closing window")
		self.root.quit()

	def handleOn(self):
		logger.debug("handleOn")

		# \n for new line \r for moving to the beginning of current line
		# self.display.notification(">- RADIO M&M  -<\n\r" + _("Got ") + str(len(self.radio.channels)) + _(" channels"), 3)
		
		# Find a way to implement this into the buttons, if it helps with the standby mode compute.
		# button.resume()

	def handleOff(self):
		logger.debug("handleOff")
		pass

	def writeInfo(self):
		radio = self.radio

		self.writeTimer = threading.Timer(1, lambda: self.writeInfo())
		self.writeTimer.start()
		self.infoText.set(
			str(time.time()) +
			"\non: " + str(radio.on) +
			"\nchannels: " + str(radio.channels) +
			"\nhoveredChannel: " + str(radio.hoveredChannel) +
			"\nlastPowerState: " + str(radio.lastPowerState) +
			"\nvolume: " + str(radio.volume) +
			"\npowerOnTime: " + str(radio.powerOnTime) +
			"\npowerOffTime: " + str(radio.powerOffTime) +
			"\nError: " + str(radio.error) +
			"\nstate: " + str(radio.state["text"]) +
			"\nchannelError: " + str(radio.channelError) +
			"\nstartedListeningTime: " + str(radio.startedListeningTime) +
			"\nsaveListeningHistory: " + str(radio.saveListeningHistory) +
			"\nshouldSendState: " + str(radio.shouldSendState)
		)

	class ResetCountdown(threading.Thread):
		def __init__(self, radio, button):
			threading.Thread.__init__(self)
			self.loadingBar = ""
			self.radio = radio
			self.button = button

		def run(self):
			self.radio.display.notification(_("RESETTING RADIO") + "\n****************")
			time.sleep(1.5)
			# Add the text to a variable so we only have to translate it once.
			confirmText = _("ARE YOU SURE?")
			confirmTextLength = len(confirmText)
			self.radio.display.notification(confirmText)
			time.sleep(0.3)

			while self.button.state == "down":
				self.loadingBar = self.loadingBar + "*"
				# self.loadingBar = self.loadingBar + "█"
				if self.radio.display.displayHeight == 1:
					self.radio.display.notification(self.loadingBar + confirmText[len(self.loadingBar) : confirmTextLength])
				else: 
					self.radio.display.notification(confirmText + "\n\r" + self.loadingBar)
				
				# Sleeping shorter than 0.3 seconds seems to make the display go corrupt...
				time.sleep(0.3)
				# time.sleep(3 / self.radio.display.displayWidth)
				
				if len(self.loadingBar) >= self.radio.display.displayWidth:
					self.radio.registration.reset()
					return