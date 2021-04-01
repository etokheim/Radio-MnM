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
		self.name = "Emulated frontend loop"
		self.radio = radio

		self.root = None
		self.start()

		self.channelSwitchDelay = config["channelSwitchDelay"]
		# There is a delay before the browsed to channel is played. This variable holds the
		# "hovered" channel.
		self.hoveredChannel = None

		# Object containing the timer which delays bumps
		self.delayedBumpTimer = None
		
		# Attach components
		if "components" in config:
			if "emulatedNavigationButton" in config["components"]:
				if config["components"]["emulatedNavigationButton"]:
					import handlers.emulatedButton as emulatedButton
					self.emulatedNavigationButton = emulatedButton.Button(self.root, "Navigation Button")

					# Listen to the button
					self.emulatedNavigationButton.addEventListener("click", lambda: self.delayBump())
					self.emulatedNavigationButton.addEventListener("longPress", lambda: self.delayBump(-1))
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
		
		self.updateUiInterval = threading.Thread(target = self.writeInfo, name = "Update UI Interval")
		self.updateUiInterval.start()

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
		while True:
			radio = self.radio

			selectedChannelName = "None"
			if radio.selectedChannel:
				selectedChannelName = radio.selectedChannel["name"]
			
			hoveredChannelName = "None"
			if self.hoveredChannel:
				hoveredChannelName = self.hoveredChannel["name"]

			self.infoText.set(
				str(round(time.time())) +
				"\non: " + str(radio.on) +
				"\nchannels: " + str(radio.channels) +
				"\nlastPowerState: " + str(radio.lastPowerState) +
				"\nvolume: " + str(radio.volume) +
				"\npowerOnTime: " + str(radio.powerOnTime) +
				"\npowerOffTime: " + str(radio.powerOffTime) +
				"\nError: " + str(radio.error) +
				"\nstate: " + str(radio.state["text"]) +
				"\nchannelError: " + str(radio.channelError) +
				"\nstartedListeningTime: " + str(radio.startedListeningTime) +
				"\nsaveListeningHistory: " + str(radio.saveListeningHistory) +
				"\nshouldSendState: " + str(radio.shouldSendState) +
				"\nchannelSwitchDelay: " + str(self.channelSwitchDelay) +
				"\nselectedChannel[name]: " + selectedChannelName +
				"\nhoveredChannel: " + hoveredChannelName
			)

			time.sleep(0.1)

	def delayBump(self, bumps = 1):
		# self.display.notification(self.hoveredChannel["name"], self.channelSwitchDelay)

		self.hoveredChannel = self.getHoveredChannelByOffset(bumps)

		if self.delayedBumpTimer:
			self.delayedBumpTimer.cancel()

		self.delayedBumpTimer = threading.Timer(self.channelSwitchDelay, self.playHoveredChannel, args=[self.hoveredChannel])
		self.delayedBumpTimer.start()
	
	def playHoveredChannel(self, channel):
		self.hoveredChannel = None
		self.radio.playChannel(channel)

	def getHoveredChannelByOffset(self, offset):
		# Number of channels to skip which remains after removing overflow.
		# (Overflow: if you are playing channel 3 of 10 and is instructed to skip 202 channels ahead,
		# you would end up on channel 205. The overflow is 200, and we should return channel 5 (3 + 2))
		remaining = (len(self.radio.channels) + offset) % len(self.radio.channels)
		if not self.hoveredChannel:
			self.hoveredChannel = self.radio.selectedChannel
		hoveredChannelIndex = self.radio.channels.index(self.hoveredChannel)
		bumpTo = 0

		if hoveredChannelIndex + remaining > len(self.radio.channels) - 1:
			bumpTo = hoveredChannelIndex - len(self.radio.channels) + remaining

		elif hoveredChannelIndex + remaining < 0:
			bumpTo = len(self.radio.channels) + hoveredChannelIndex + remaining

		else:
			bumpTo = hoveredChannelIndex + remaining

		# logger.debug("offset " + str(offset) + ", bumping to: " + str(bumpTo))
		return self.radio.channels[bumpTo]


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