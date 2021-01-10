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
		
				self.rotary = rotaryPolling.Rotary(props["GPIO"]["clk"], props["GPIO"]["data"])
				self.rotary.addEventListener("left", radio.bump(-1))
				self.rotary.addEventListener("right", radio.bump())

			if "navigationButton" in config["components"]:
				self.button = handlers.button.Button(gpioPin)

				self.button.addEventListener("click", radio.bump())
				# self.button.addEventListener("press", self.buttonDownHandler)
				# self.button.addEventListener("release", self.buttonUpHandler)
				self.button.addEventListener("longPress", radio.bump(-1))
				# self.button.addEventListener("veryLongPress", self.buttonVeryLongPressHandler)
	
			if "volumeRotary" in config["components"]:
				import components.volumeRotary as volumeRotary
				self.volumeRotary = volumeRotary.VolumeRotary(radio, config["components"]["volumeRotary"])

			if "volumeButtons" in config["components"]:
				import components.volumeButtons as volumeButtons
				self.volumeButtons = volumeButtons.VolumeButtons(radio, config["components"]["volumeButtons"])

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