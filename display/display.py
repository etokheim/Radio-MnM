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

# def write(message):
# 	# Split message up into an array of lines
# 	printMessage = message.replace("\r", "")
# 	lines = printMessage.split("\n")

# 	# If the message fits on the screen, return without doing anything to the message
# 	scrollingLines = []
# 	for line in lines:
# 		if len(line) > config.displayWidth:
# 			scrollingLines.append(line)

# 	if len(scrollingLines) == 0:
# 		print("Message fits on the screen, no need for scrolling")
# 		actualWrite(message)
# 		return

# 	# If we have lines that need scrolling
# 	# scrollTextThread = threading.Thread(target=scrollText, args=("scrollingTextThread", lines))
# 	# scrollTextThread.start()

# 	actualWrite(formattedMessage)

class Display(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.notification = ""
		self.standardContent = "Standard, but very, very loooong Content\nLine two is also very long!"
		self.notificationExpireTime = False
		self.running = True
		self.currentlyDisplaying = ""
		self.lines = []
		self.croppedLines = []
		self.lineOffset = 0
		# For how many steps we should pause when displaying the end of the line
		self.endPauseSteps = 4

	def run(self):
		while self.running:
			# Clear expired notifications
			# print("self.notificationExpireTime: " + str(self.notificationExpireTime))
			if int(round(time.time() * 1000)) >= self.notificationExpireTime and self.notificationExpireTime != False:
				print("Notification expired!")
				self.notification = ""
				self.notificationExpireTime = False

			if self.notification != "":
				self.currentlyDisplaying = self.notification
			else:
				self.currentlyDisplaying = self.standardContent

			self.displayMessage()
			time.sleep(0.5)

	def displayMessage(self):
		stripCarriages = self.currentlyDisplaying.replace("\r", "")
		self.lines = stripCarriages.split("\n")
		composedMessage = ""
		self.croppedLines = []
		longestLineLength = 0

		for i in range(len(self.lines)):
			line = self.lines[i]

			# Assign the length as the longest line if it's longer than the last measured one
			if len(line) > longestLineLength:
				longestLineLength = len(line)

			# If the line doesn't fit
			if len(line) > config.displayWidth:
				# If we are not showing the end of the line
				if len(line) - self.lineOffset > config.displayWidth:
					print("Get characters between " + str(self.lineOffset) + " and " + str(self.lineOffset + config.displayWidth))
					self.croppedLines.append(line[self.lineOffset:self.lineOffset + config.displayWidth])
				# If we are showing the end of the line, stop scrolling
				else:
					self.croppedLines.append(line[len(line) - config.displayWidth:len(line)])
			else:
				self.croppedLines.append(line)

			composedMessage = composedMessage + self.croppedLines[i]
			
			# If it's not the last line, add a new line
			if i + 1 != len(self.lines):
				composedMessage = composedMessage + "\n\r"
		
		print("self.lineOffset: " + str(self.lineOffset) + ", longestLineLength: " + str(longestLineLength))
		if self.lineOffset + config.displayWidth - self.endPauseSteps < longestLineLength:
			self.lineOffset = self.lineOffset + 1
		else:
			self.lineOffset = 0

		self.write(composedMessage)



	def write(self, message):
		print("-------------------")
		print("| " + message + " |")
		print("-------------------")

	def scrollText(self, name, line):
		print("Text to scroll")
		print(line[0])
		print(line[1])

display = Display()
display.start()

# def actualWrite(message):
# 	clear()
	
# 	# Split message up into an array of lines
# 	printMessage = message.replace("\r", "")
# 	lines = printMessage.split("\n")

# 	if config.debug:
# 		# Simulate display
# 		# TODO: Clean this up
# 		firstLine = "│      " + lines[0]

# 		# Add n spaces to the end of the message, where n = the number of character spaces left on the
# 		# simulated screen.
# 		for i in range(displayWidth - len(lines[0])):
# 			firstLine = firstLine + " "
		
# 		# Then add some padding plus the display edge.
# 		firstLine = firstLine + "      │"

# 		# Do the same for the second line
# 		secondLine = "│                            │"

# 		if len(lines) > 1:
# 			secondLineLength = len(lines[1])
# 			secondLine = "│      " + lines[1]
		
# 			for i in range(displayWidth - len(lines[1]):
# 				secondLine = secondLine + " "
			
# 			secondLine = secondLine + "      │"

# 		print("┌────────────────────────────┐")
# 		print("│                            │")
# 		print  (         firstLine          )
# 		print  (         secondLine         )
# 		print("│                            │")
# 		print("└────────────────────────────┘")
	
# 	if config.raspberry:
# 		lcd.write_string(message)


# def writeStandardContent():
# 	if currentMessage == "":
# 		lineOne = config.radio.selectedChannel["name"]
# 		lineTwo = str(config.radio.media.get_meta(12))

# 		write(lineOne + "\n\r" + lineTwo)

# class oldMessagesCollector(threading.Thread):
# 	def __init__(self):
# 		threading.Thread.__init__(self)

# 	def run(self):
# 		global currentMessageExpires, currentMessage
# 		time.sleep(4)
# 		while True:
# 			if currentMessageExpires != False and int(round(time.time() * 1000)) >= currentMessageExpires:
# 				print(currentMessage + " expired")
# 				currentMessage = ""
# 				currentMessageExpires = False
# 				writeStandardContent()

# 			time.sleep(0.2)

# listenRadio = oldMessagesCollector()
# listenRadio.start()

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
