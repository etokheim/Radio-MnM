import logging
logger = logging.getLogger("Radio_mnm")
from config.config import config
from handlers import pollingSwitch
from handlers import rotaryPolling
import handlers.button
import threading

_ = config["getLanguage"].gettext

class CharacterDisplay():
	def __init__(self, radio):
		self.radio = radio
		self.delayTurningOffBacklight = None
		self.delayedBumpTimer = None
		self.hoveredChannel = None
		self.channelSwitchDelay = config["channelSwitchDelay"]
		self.environmentData = None
		
		# Attach components
		# TODO: Support multiple displays
		if "components" in config:
			if "displays" in config["components"]:
				displays = config["components"]["displays"]

				for display in displays:
					import components.displayCharacterLcd as displayCharacterLcd
					self.display = displayCharacterLcd.Display(radio, display)

			if "navigationRotary" in config["components"]:
				# Get the props
				props = config["components"]["navigationRotary"]	
				
				# Check the props
				assert type(props["GPIO"]["clk"]) == int, "NavigationRotary's clk pin is not an int. Please check your config.yml"
				assert type(props["GPIO"]["data"]) == int, "NavigationRotary's data pin is not an int. Please check your config.yml"
		
				self.navigationRotary = rotaryPolling.Rotary(props["GPIO"]["clk"], props["GPIO"]["data"])
				self.navigationRotary.addEventListener("left", self.delayBump, args=[-1])
				self.navigationRotary.addEventListener("right", self.delayBump)

			if "navigationButton" in config["components"]:
				# Get pin and validate it
				gpioPin = config["components"]["navigationButton"]["GPIO"]
				assert type(gpioPin) == int, "NavigationButton's pin is not an int. Please check your config.yml"

				# Create the button		
				self.navigationButton = handlers.button.Button(gpioPin)

				self.navigationButton.addEventListener("click", self.delayBump())
				# self.navigationButton.addEventListener("press", self.buttonDownHandler)
				# self.navigationButton.addEventListener("release", self.buttonUpHandler)
				self.navigationButton.addEventListener("longPress", self.delayBump, args=[-1])
				# self.navigationButton.addEventListener("veryLongPress", self.buttonVeryLongPressHandler)
	
			if "volumeRotary" in config["components"]:
				# Get the props
				props = config["components"]["volumeRotary"]	
					
				# Check the props
				assert type(props["GPIO"]["clk"]) == int, "VolumeRotary's clk pin is not an int. Please check your config.yml"
				assert type(props["GPIO"]["data"]) == int, "VolumeRotary's data pin is not an int. Please check your config.yml"
		
				self.volumeRotary = rotaryPolling.Rotary(props["GPIO"]["clk"], props["GPIO"]["data"])
				self.volumeRotary.addEventListener("left", self.volumeDownHandler)
				self.volumeRotary.addEventListener("right", self.volumeUpHandler)

			if "volumeButtons" in config["components"]:
				pass

			if "powerSwitch" in config["components"]:
				gpioPin = config["components"]["powerSwitch"]["GPIO"]
				
				# Create a new switch
				self.powerSwitch = pollingSwitch.pollingSwitch(radio, gpioPin)
		
				# Attach event listeners
				self.powerSwitch.addEventListener("on", radio.powerOn)
				self.powerSwitch.addEventListener("off", radio.powerOff)
		
			if "powerButton" in config["components"]:
				gpioPin = config["components"]["powerButton"]["GPIO"]

				import handlers.button as button	
				self.powerButton = button.Button(gpioPin)

				# Attach event listener
				self.powerButton.addEventListener("click", radio.togglePower)

			if "dht22" in config["components"]:
				props = config["components"]["dht22"]
				assert type(props["GPIO"]) == int, "The DHT22's GPIO pin is not an int. Please check your config.yml"
				import components.dht22 as dht22
				self.dht22 = dht22.Dht22(radio, config["components"]["dht22"]["GPIO"])

				self.dht22.addEventListener("update", self.handleDht22Update)
				# self.dht22.addEventListener("error", self.handleDht22Update)

		
		# Add event listeners
		radio.addEventListener("on", self.handleOn)
		radio.addEventListener("off", self.handleOff)
		radio.addEventListener("volume", self.displayVolumeLevel)

		# Only listen to meta events if the display height is more than one
		if self.display.displayHeight > 1:
			radio.addEventListener("meta", self.handleNewMeta)

	def displayVolumeLevel(self, event):
		volume = event["volume"]

		# Display volume level
		progressBarStyle = "*"

		volumeBarWidth = self.display.displayWidth
		if self.display.displayHeight == 1:
			volumeBarWidth = self.display.displayWidth - 4

		volumeBar = ""
		numberOfBars = round(volumeBarWidth / 100 * volume)
		
		for i in range(volumeBarWidth):
			if i < numberOfBars:
				volumeBar = volumeBar + progressBarStyle
			else:
				volumeBar = volumeBar + " "
		
		if self.display.displayHeight == 1:
			self.display.notification("Vol " + volumeBar)
		else:
			self.display.notification("Volume\n\r" + volumeBar)

	def handleDht22Update(self, event):
		self.environmentData = event

		if not self.radio.on:
			self.display.writeStandardContent(self.generateStandardContent())

	def handleNewMeta(self, event):
		# Clear the second line just for a second to let the user see that there's new content, not
		# just a scroll or a scroll reset.

		# Display only the channel name
		self.display.writeStandardContent(self.radio.selectedChannel["name"])

		standardContent = self.generateStandardContent()

		# Then after a delay, display everything again
		fullStandardContent = threading.Timer(0.25, self.display.writeStandardContent, args=[standardContent])
		fullStandardContent.start()

		# # If there is a new text to display
		# if self.lastDisplayedMessage != self.currentlyDisplayingMessage:
		# 	# Reset the text offset (scroll position)
		# 	self.scrollOffset = 0 - self.displayScrollingStartPauseSteps
			
		# 	# Only do this if displaying channel info
		# 	if messageType == "channelInfo" and self.displayHeight >= 2 and self.radio.on:
		# 		# When the text changes, "clear the second line" for å brief moment, so the user
		# 		# more easily can understand that a new text was inserted.
		# 		# Crap, this only works for channels, but notifications are also parsed through here...
		# 		self.write(lines[0])

		# 	time.sleep(0.25)

	def generateStandardContent(self):
		standardContent = None

		# Check if there's a prioritized message:
		prioritizedMessage = None
		state = self.radio.state

		# 1. Are we updating?
		if self.radio.updating:
			prioritizedMessage = self.radio.updating["text"]

		# 2. Any errors?
		elif self.radio.error:
			prioritizedMessage = self.radio.error["text"]

		# 3. Any channel errors?
		elif self.radio.channelError:
			prioritizedMessage = self.radio.channelError["text"]

		if self.display.displayHeight == 1:
			# If there's a prioritized message, display that
			if prioritizedMessage:
				standardContent = prioritizedMessage
			else:
				# Else, if the radio is on, display the current channel's name
				if self.radio.on:
					standardContent = self.radio.selectedChannel["name"]
				
				# If the radio is off
				else:
					# Do we have environment data?
					if self.environmentData:
						# If we have both temps and humidity, display it
						if self.environmentData["temperature"] != None and self.environmentData["humidity"] != None:
							standardContent = "T: " + str(self.radio.temperatureAndHumidity.temperature) + "C, H: " + str(self.radio.temperatureAndHumidity.humidity) + "%"

					# Display the time
					else:
						standardContent = "The time"
		
		# Display is taller than 1 line
		else:
			if self.radio.on:
				firstLine = self.radio.selectedChannel["name"]
				
				if prioritizedMessage:
					secondLine = prioritizedMessage
				elif state["code"] != "playing":
					secondLine = state["text"]
				else:
					secondLine = self.radio.media.get_meta(12)
				
				standardContent = firstLine + "\r\n" + secondLine
			
			# If the radio is off
			else:
				# Do we have environment data?
				if self.environmentData:
					# If we have both temps and humidity, display it
					if self.environmentData["temperature"] != None and self.environmentData["humidity"] != None:
						standardContent = 	"Temp: " + str(self.environmentData["temperature"]) + "C\r\n" + \
											"Humidity: " + str(self.environmentData["humidity"]) + "%"

				# Display the time
				else:
					standardContent = "The time"
		
		return standardContent


	def handleOn(self):
		logger.debug("handleOn")
		self.display.lcd.backlight_enabled = True

		# Cancel the timer which would turn off the backlight if it is running
		if self.delayTurningOffBacklight:
			self.delayTurningOffBacklight.cancel()
			self.delayTurningOffBacklight = None

		# Turn the display loop on again if it was off
		# if not self.radio.offContent:
			# self.display.resume()

		# \n for new line \r for moving to the beginning of current line
		self.display.notification(">- RADIO M&M  -<\n\r" + _("Got ") + str(len(self.radio.channels)) + _(" channels"), 3)
		self.display.writeStandardContent(self.generateStandardContent())
		
		# Find a way to implement this into the buttons, if it helps with the standby mode compute.
		# button.resume()

	def handleOff(self):
		logger.debug("handleOff")

		if not config["powerOffDisplayLightsDuration"]:
			self.display.lcd.backlight_enabled = False

		self.display.writeStandardContent(self.generateStandardContent())
					
		# Reinit the display to battle the corrupted display issue
		self.display.lcd = None
		self.display.lcd = self.display.initializeLcd()

		# Stop the display loop when off if we don't want to display content
		# if not self.radio.offContent:
		# 	self.display.pause()

		# Find a way to implement this into the buttons, if it helps with the standby mode compute.
		# button.pause()

		# Turn off the backlight after a delay
		self.delayTurningOffBacklight = threading.Timer(config["powerOffDisplayLightsDuration"], self.display.turnOffBacklight)
		self.delayTurningOffBacklight.start()
	
	def volumeDownHandler(self):
		logger.debug("Volume rotaryLeftHandler")
		
		if self.radio.on:
			self.radio.setVolume(self.radio.volume - 10)

	def volumeUpHandler(self):
		logger.debug("Volume rotaryRightHandler")
		
		if self.radio.on:
			self.radio.setVolume(self.radio.volume + 10)

	def delayBump(self, bumps = 1):
		if not self.radio.on:

			return

		self.hoveredChannel = self.getHoveredChannelByOffset(bumps)

		self.display.notification(self.hoveredChannel["name"], self.channelSwitchDelay)

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