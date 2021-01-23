from config.config import config

class EmulatedFrontend():
	def __init__(self, radio):
		self.radio = radio

		# Attach components
		if "components" in config:
			if "emulatedNavigationButton" in config["components"]:
				import components.emulatedNavigationButton as emulatedNavigationButton
				self.emulatedNavigationButton = emulatedNavigationButton.EmulatedNavigationButton(radio)
				
		print("----------------------")
		print("----------------------")
		print("Frontend is initiated!")
		print("----------------------")
		print("----------------------")