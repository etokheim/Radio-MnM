from config import config
import threading
import time

if config.raspberry == True:
	from RPi import GPIO
else:
	from EmulatorGUI.EmulatorGUI import GPIO

def clear():
	if config.raspberry == False:
		print("│ - -  Display cleared   - - │")
	
	if config.raspberry:
		lcd.clear()


currentMessage = ""
currentMessageExpires = 0

def notification(message, duration = 2):
	# global currentMessage, currentMessageExpires
	# currentMessage = message
	# currentMessageExpires = int(round(time.time() * 1000)) + duration * 1000
	display.notification = message
	display.notificationExpireTime = int(round(time.time() * 1000)) + duration * 1000

	display.write(message)

class Display(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.notification = ""
		self.standardContent = ""
		self.notificationExpireTime = False
		self.running = True
		self.currentlyDisplayingMessage = ""
		
		self.scrollOffset = 0 - config.displayScrollingStartPauseSteps
		self.lastDisplayedMessage = ""
		self.lastDisplayedCroppedMessage = ""

	def run(self):
		time.sleep(2)
		while self.running:
			# Set standard content
			self.standardContent = config.radio.selectedChannel["name"] + "\n\r" + str(config.radio.media.get_meta(12))

			# Clear expired notifications
			# print("self.notificationExpireTime: " + str(self.notificationExpireTime))
			if int(round(time.time() * 1000)) >= self.notificationExpireTime and self.notificationExpireTime != False:
				print("Notification expired")
				self.notification = ""
				self.notificationExpireTime = False

			if self.notification != "":
				self.currentlyDisplayingMessage = self.notification
			else:
				self.currentlyDisplayingMessage = self.standardContent

			self.displayMessage()
			time.sleep(config.displayScrollSpeed)

	def displayMessage(self):
		# If there is a new text to display, reset the text offset
		if self.lastDisplayedMessage != self.currentlyDisplayingMessage:
			self.scrollOffset = 0 - config.displayScrollingStartPauseSteps
			
		stripCarriages = self.currentlyDisplayingMessage.replace("\r", "")
		lines = stripCarriages.split("\n")
		composedMessage = ""
		croppedLines = []
		longestLineLength = 0
		displayWidth = config.displayWidth

		for i in range(len(lines)):
			line = lines[i]
			lineLength = len(line)

			# Assign the length as the longest line if it's longer than the last measured one
			if lineLength > longestLineLength:
				longestLineLength = lineLength

			# If the line doesn't fit
			if lineLength > displayWidth:

				# Pause scrolling if scrollOffset is less than zero. This is how self.displayScrollingStartPauseSteps is implemented
				if self.scrollOffset >= 0:

					# If we are not showing the end of the line, scroll
					if lineLength - self.scrollOffset > displayWidth:
						croppedLines.append(
							line[self.scrollOffset:self.scrollOffset + displayWidth]
						)
					
					else:
						# If we are showing the end of the line, stop scrolling
						croppedLines.append(
							line[lineLength - displayWidth:lineLength]
						)

				else:
					# If self.scrollOffset is less than zero (pausing), then display the start of the message
					# until it's zero or higher
					croppedLines.append(line[0:displayWidth])

			else:
				# If line fits
				croppedLines.append(line)

			composedMessage = composedMessage + croppedLines[i]
			
			# If it's not the last line, add a newline
			if i + 1 != len(lines):
				composedMessage = composedMessage + "\n\r"
		
		# Increase the scroll offset as long as we are not at the end of the line
		# If we are at the end of the line, we keep scrolling however for N steps.
		# Since scrolling further than the last line has no visual effect, this
		# is used to make a pause to give the user time to finish reading.
		# N (aka the pause) = config.displayScrollingStopPauseSteps
		if self.scrollOffset + displayWidth - config.displayScrollingStopPauseSteps <= longestLineLength:
			self.scrollOffset = self.scrollOffset + 1
		else:
			# Reset the scrollOffset
			self.scrollOffset = 0 - config.displayScrollingStartPauseSteps

		# TODO: Fix notifications displaying twice:
		# If the displayed message was new, set the lastDisplayedMessages to
		# currentlyDisplayingMessages. If we don't do this, all notifications
		# will be displayed twice as lastDisplayedMessages never will be equal
		# to currentlyDisplayedMessages
		# if self.lastDisplayedMessage != self.currentlyDisplayingMessage:
		# 	self.lastDisplayedMessage = self.currentlyDisplayingMessage
		# 	self.lastDisplayedCroppedMessage = composedMessage

		# Only write to the display if it's not the same as what's being displayed
		if composedMessage != self.lastDisplayedCroppedMessage:
			self.write(composedMessage)

		self.lastDisplayedMessage = self.currentlyDisplayingMessage

		# We need this variable in order not overwrite the display with the same
		# message. We cannot use lastDisplayedMessage as that one is not cropped,
		# and wouldn't work when the composedMessage is cropped.
		self.lastDisplayedCroppedMessage = composedMessage
			

	def write(self, message):
		# Simulate a display in the terminal, if we are running in debug mode
		if config.debug:
			self.writeToSimulatedScreen(message)
		
		# Write to the actual display, if we are running on a Raspberry Pi
		if config.raspberry:
			lcd.write_string(message)

	def scrollText(self, name, line):
		print("Text to scroll")
		print(line[0])
		print(line[1])

	def writeToSimulatedScreen(self, message):
		# Split message up into an array of lines
		printMessage = message.replace("\r", "")
		lines = printMessage.split("\n")

		# Simulate display
		# TODO: Clean this up
		firstLine = "│      " + lines[0]

		# Add n spaces to the end of the message, where n = the number of character spaces left on the
		# simulated screen.
		for i in range(config.displayWidth - len(lines[0])):
			firstLine = firstLine + " "
		
		# Then add some padding plus the display edge.
		firstLine = firstLine + "      │"

		# Do the same for the second line
		secondLine = "│                            │"

		if len(lines) > 1:
			secondLine = "│      " + lines[1]
		
			for i in range(config.displayWidth - len(lines[1])):
				secondLine = secondLine + " "
			
			secondLine = secondLine + "      │"

		print("┌────────────────────────────┐")
		print("│                            │")
		print  (         firstLine          )
		print  (         secondLine         )
		print("│                            │")
		print("└────────────────────────────┘")

display = Display()
display.start()

if config.raspberry:
	# We are using the GPIO numbering scheme
	lcd = CharLCD(cols=config.displayWidth,
				rows=config.displayHeight,
				pin_rs=26,
				pin_e=19,
				pins_data=[13, 6, 5, 11],
				numbering_mode=GPIO.BCM,
				compat_mode = True,
				dotsize = 8,
				charmap = 'A02'
	)

	lcd.clear()
	lcd.cursor_pos = (0, 0)
