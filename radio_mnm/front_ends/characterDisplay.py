from config.config import config
from handlers import rotaryPolling
import handlers.button

class CharacterDisplay():
	def __init__(self, radio):
		# Attach components
		# TODO: Support multiple displays
		if "components" in config:
			if "displays" in config["components"]:
				displays = config["components"]["displays"]

				for display in displays:
					import components.displayCharacterLcd as display
					self.display = display.Display(radio, display)

			if "navigationRotary" in config["components"]:
				# Get the props
				props = config["components"]["navigationRotary"]	
				
				# Check the props
				assert type(props["GPIO"]["clk"]) == int, "NavigationRotary's clk pin is not an int. Check your config.yml"
				assert type(props["GPIO"]["data"]) == int, "NavigationRotary's data pin is not an int. Check your config.yml"
		
				self.navigationRotary = rotaryPolling.Rotary(props["GPIO"]["clk"], props["GPIO"]["data"])
				self.navigationRotary.addEventListener("left", radio.bump(-1))
				self.navigationRotary.addEventListener("right", radio.bump())

			if "navigationButton" in config["components"]:
				# Get pin and validate it
				gpioPin = config["components"]["navigationButton"]["GPIO"]
				assert type(gpioPin) == int, "NavigationButton's pin is not an int. Check your config.yml"

				# Create the button		
				self.navigationButton = handlers.button.Button(gpioPin)

				self.navigationButton.addEventListener("click", radio.bump())
				# self.navigationButton.addEventListener("press", self.buttonDownHandler)
				# self.navigationButton.addEventListener("release", self.buttonUpHandler)
				self.navigationButton.addEventListener("longPress", radio.bump(-1))
				# self.navigationButton.addEventListener("veryLongPress", self.buttonVeryLongPressHandler)
	
			if "volumeRotary" in config["components"]:
				# Get the props
				props = config["components"]["volumeRotary"]	
					
				# Check the props
				assert type(props["GPIO"]["clk"]) == int, "VolumeRotary's clk pin is not an int. Check your config.yml"
				assert type(props["GPIO"]["data"]) == int, "VolumeRotary's data pin is not an int. Check your config.yml"
		
				self.volumeRotary = rotaryPolling.Rotary(props["GPIO"]["clk"], props["GPIO"]["data"])
				self.volumeRotary.addEventListener("left", self.volumeDownHandler)
				self.volumeRotary.addEventListener("right", self.volumeUpHandler)

			if "volumeButtons" in config["components"]:
				pass

			if "powerSwitch" in config["components"]:
				import components.powerSwitch as powerSwitch
				self.powerSwitch = powerSwitch.PowerSwitch(radio, config["components"]["powerSwitch"])

			if "powerButton" in config["components"]:
				import components.powerButton as powerButton
				self.powerButton = powerButton.powerButton(radio, config["components"]["powerButton"])

			if "dht22" in config["components"]:
				import components.dht22 as dht22
				self.dht22 = dht22.Dht22(radio, config["components"]["dht22"])

			if "emulatedNavigationButton" in config["components"]:
				import components.emulatedNavigationButton as emulatedNavigationButton
				self.emulatedNavigationButton = emulatedNavigationButton.EmulatedNavigationButton(radio)


	def volumeDownHandler(self):
		logger.debug("Volume rotaryLeftHandler")
		
		if self.radio.on:
			self.radio.setVolume(self.radio.volume - 10)
			self.radio.displayVolumeLevel()

	def volumeUpHandler(self):
		logger.debug("Volume rotaryRightHandler")
		
		if self.radio.on:
			self.radio.setVolume(self.radio.volume + 10)
			self.radio.displayVolumeLevel()
