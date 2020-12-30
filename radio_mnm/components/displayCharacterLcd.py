import logging
logger = logging.getLogger("Radio_mnm")
from config.config import config
import threading
import time
import gettext
import sys
from helpers import helpers

_ = config["getLanguage"].gettext

from RPi import GPIO
from RPLCD.gpio import CharLCD

class Display(threading.Thread):
	def __init__(self, radio, setup):
		threading.Thread.__init__(self)

		self.setup = setup

		if setup["type"] != "Character LCD":
			raise Exception("Invalid display type: " + setup["type"] + ". Check your config.yml")

		self.notificationMessage = ""
		self.standardContent = ""
		self.notificationExpireTime = False
		self.running = True
		# When paused is set, the thread will run, when it's not set, the thread will wait
		self.pauseEvent = threading.Event()
		self.currentlyDisplayingMessage = ""

		# For how many steps we should pause when displaying the start of the line (1 step = displayScrollSpeed)
		self.displayScrollingStartPauseSteps = 12

		# For how many steps we should pause when displaying the end of the line (1 step = displayScrollSpeed)
		self.displayScrollingStopPauseSteps = 8

		# Time between scrolls
		self.displayScrollSpeed = 0.2 # seconds
		
		self.scrollOffset = 0 - self.displayScrollingStartPauseSteps
		self.lastDisplayedMessage = ""
		self.lastDisplayedCroppedMessage = ""

		# Render a virtual display in the console output
		self.virtualDisplay = False

		# Amount of characters, not pixels
		self.displayWidth = setup["width"]
		self.displayHeight = setup["height"]

		# Weird display quirk, where one line is two lines for the computer. I guess this is due to
		# some cost saving initiative in display production.
		self.oneDisplayLineIsTwoLines = setup["oneDisplayLineIsTwoLines"]

		self.radio = radio

		# Compensate for a weird display quirk. Read more in the comments above
		if setup["oneDisplayLineIsTwoLines"]:
			self.actualDisplayWidth = setup["width"] // 2
			self.actualDisplayHeight = setup["height"] * 2
		else:
			self.actualDisplayWidth = setup["width"]
			self.actualDisplayHeight = setup["height"]

		self.lcd = self.initializeLcd()

		# Turn off backlight if the radio is off
		if not self.radio.on:
			self.lcd.backlight_enabled = False
		
		self.resume()

		# Custom characters
		self.ae = (
			0b00000,
			0b00000,
			0b01011,
			0b10101,
			0b10111,
			0b10100,
			0b01011,
			0b00000
		)

		self.AE = (
			0b00111,
			0b01100,
			0b10100,
			0b10111,
			0b11100,
			0b10100,
			0b10111,
			0b00000
		)

		self.oe = (
			0b00000,
			0b00000,
			0b01111,
			0b10011,
			0b10101,
			0b11001,
			0b11110,
			0b00000
		)

		self.OE = (
			0b01111,
			0b10001,
			0b10011,
			0b10101,
			0b11001,
			0b10001,
			0b11110,
			0b00000
		)

		self.aa = (
			0b00100,
			0b01010,
			0b01110,
			0b00001,
			0b01111,
			0b10001,
			0b01111,
			0b00000
		)

		self.AA = (
			0b00100,
			0b01010,
			0b01110,
			0b10001,
			0b11111,
			0b10001,
			0b10001,
			0b00000
		)

		self.g = (
			0b00000,
			0b00000,
			0b01111,
			0b10001,
			0b10001,
			0b01111,
			0b00001,
			0b01110
		)

		# TODO: Check if these should be moved into the initialize lcd function
		self.lcd.create_char(0, self.ae)
		self.lcd.create_char(1, self.AE)
		self.lcd.create_char(2, self.oe)
		self.lcd.create_char(3, self.OE)
		self.lcd.create_char(4, self.aa)
		self.lcd.create_char(5, self.AA)
		self.lcd.create_char(6, self.g)

	def run(self):
		# Wait, if the thread is set on hold
		self.pauseEvent.wait()
		
		while self.running:
			# Wait, if the thread is set on hold
			self.pauseEvent.wait()

			# Set standard content
			self.writeStandardContent()

			if self.radio.on:
				time.sleep(self.displayScrollSpeed)
			else:
				# Turn off the display lights after the delay has elapsed
				if self.lcd.backlight_enabled:
					if int(round(time.time() * 1000)) - self.radio.turnOffTime > config["powerOffDisplayLightsDuration"] * 1000:
						self.lcd.backlight_enabled = False
				
				time.sleep(1)

	def stop(self):
		self.clear()
		self.running = False
		logger.warning("Stopped display")

	def pause(self):
		self.clear()
		self.pauseEvent.clear()
		logger.debug("Paused display handling loop")

	def resume(self):
		self.pauseEvent.set()
		logger.debug("Resumed display handling loop")

	def initializeLcd(self):
		return CharLCD(
			# (int) Number of columns per row (usually 16 or 20). Default: 20.
			cols=self.actualDisplayWidth,
			
			# (int) Number of display rows (usually 1, 2 or 4). Default: 4.
			rows=self.actualDisplayHeight,
			
			pin_rs=self.setup["GPIO"]["rs"],
			
			pin_e=self.setup["GPIO"]["en"],
			
			pins_data=[self.setup["GPIO"]["data4"], self.setup["GPIO"]["data5"], self.setup["GPIO"]["data6"], self.setup["GPIO"]["data7"]],
			
			numbering_mode=GPIO.BCM,
			
			compat_mode = self.setup["lcdCompatibillityMode"],
			
			# (int) Some 1 line displays allow a font height of 10px. Allowed: 8 or 10.
			dotsize = self.setup["dotSize"],
			
			# The character map used. Depends on your LCD. This must be either A00 or A02 or ST0B.
			charmap = self.setup["lcdCharacterMap"],
			
			# (bool) – Whether or not to automatically insert line breaks. Default: True.
			# Note: If we turn it on, it seems like we can't fill the last character of the lines.
			# throws the following error:
			# ValueError: Cursor position (1, 16) invalid on a 2x16 LCD.
			#
			# 16 is the 17th character, as 0, 0 is the first character of the first line. However
			# what we tried to display was "f The World Was ", which is 16 characters long and should
			# therefor fit on the display...I don't know why we get this error, but if i never populate
			# the last character (of either lines), the program runs fine. (When I do this, the display
			# of course doesn't use the last character space, which is a waste). Turning auto_linebreaks
			# on seems to fix the issue, so we shouldn't use more time on this.
			# 
			# We used extra time on this because we thought it might have contributed to the character 
			# corruption, but since it still happened when turning the auto_linebreaks off and limiting
			# the display to 15 characters it seems unlikely.
			auto_linebreaks = True,
			
			# (bool) – Whether the backlight is enabled initially. Default: True.
			backlight_enabled = True,

			pin_backlight = self.setup["GPIO"]["backlight"],

			backlight_mode = self.setup["backlightMode"]
		)

	def writeStandardContent(self):
		if self.radio.on:
			# Set standard content
			# Selected channel can be None when the self.radio is on, only right after a reset.
			if self.radio.selectedChannel is not None:
				# Format standard content based on screen size
				# Set the second line's content:
				if self.displayHeight >= 2:
					# By default, display the meta (ie. [Song] - [Artist])
					secondLine = self.radio.media.get_meta(12)
					
					# Get the self.radio's state
					state = self.radio.state

					# Display any errors
					if self.radio.updating:
						secondLine = self.radio.updating["text"]

					# Display any errors
					elif self.radio.error:
						secondLine = self.radio.error["text"]

					# Display any channel errors
					elif self.radio.channelError:
						secondLine = self.radio.channelError["text"]

					# Display any special states
					elif state["code"] != "playing":
						secondLine = state["text"]

					# Meta can be None for a second after the channel starts playing (or if it's actually empty)
					elif secondLine is None:
						secondLine = ""

					self.standardContent = self.radio.selectedChannel["name"] + "\n\r" + str(secondLine)
				else:
					self.standardContent = self.radio.selectedChannel["name"]
			elif self.standardContent == "":
				self.standardContent = _("No channels")
		# The radio is off
		else:
			if self.radio.temperatureAndHumidity:
				if int(time.time() * 1000) - self.radio.temperatureAndHumidity.lastUpdateTime < 10000:
					self.standardContent = "Temp: " + str(self.radio.temperatureAndHumidity.temperature) + "C\r\nHumidity: " + str(self.radio.temperatureAndHumidity.humidity) + "%"
				else:
					self.standardContent = _("Couldn't get\n\rtemperature")

		# Clear expired notifications
		if int(round(time.time() * 1000)) >= self.notificationExpireTime and self.notificationExpireTime != False:
			self.notificationMessage = ""
			self.notificationExpireTime = False

		# TODO: Maybe it's better now to send the message as a parameter instead of setting
		# it to "currentlyDisplayingMessage"?
		if self.notificationMessage:
			self.currentlyDisplayingMessage = self.notificationMessage
			self.displayMessage()
		else:
			self.currentlyDisplayingMessage = self.standardContent
			self.displayMessage("channelInfo")

	# A notification has a limited lifespan. It is displayed for a set duration in seconds (defaults to 2).
	# When a notification expires, the standard content is displayed. Standard content is what's playing etc.
	def notification(self, message, duration = 2):
		self.notificationMessage = message
		self.notificationExpireTime = int(round(time.time() * 1000)) + duration * 1000

		self.displayMessage()

	# Clears the display
	def clear(self):
		if self.virtualDisplay:
			print("│ - -  Display cleared   - - │")
		
		self.lcd.clear()

	def displayMessage(self, messageType="notification"):
		stripCarriages = self.currentlyDisplayingMessage.replace("\r", "")
		lines = stripCarriages.split("\n")

		# If there is a new text to display
		if self.lastDisplayedMessage != self.currentlyDisplayingMessage:
			# Reset the text offset (scroll position)
			self.scrollOffset = 0 - self.displayScrollingStartPauseSteps
			
			# Only do this if displaying channel info
			if messageType == "channelInfo" and self.displayHeight >= 2 and self.radio.on:
				# When the text changes, "clear the second line" for å brief moment, so the user
				# more easily can understand that a new text was inserted.
				# Crap, this only works for channels, but notifications are also parsed through here...
				self.write(lines[0])

			time.sleep(0.25)
			
		composedMessage = ""
		croppedLines = []
		longestLineLength = 0
		displayWidth = self.displayWidth

		loopTimes = len(lines)
		if loopTimes > self.displayHeight:
			loopTimes = self.displayHeight

		for i in range(loopTimes):
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
			if i + 1 != loopTimes:
				composedMessage = composedMessage + "\n\r"
		
		# Increase the scroll offset as long as we are not at the end of the line
		# If we are at the end of the line, we keep scrolling however for N steps.
		# Since scrolling further than the last line has no visual effect, this
		# is used to make a pause to give the user time to finish reading.
		# N (aka the pause) = self.displayScrollingStopPauseSteps
		if self.scrollOffset + displayWidth - self.displayScrollingStopPauseSteps <= longestLineLength:
			self.scrollOffset = self.scrollOffset + 1
		else:
			# Reset the scrollOffset
			self.scrollOffset = 0 - self.displayScrollingStartPauseSteps

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
		self.clear()

		# Simulate a display in the terminal, if we are running in debug mode
		# Do not directly use this function to write to the display. Use notification()
		if self.virtualDisplay:
			self.writeToSimulatedScreen(message)
		
		# Write message to the actual display
		# Handle weir display quirk, where one line in the code only refers to half a line on the actual
		# display. Ie.: to fill a 16x1 display, you have to do 12345678\n90123456
		if self.oneDisplayLineIsTwoLines:
			stripCarriages = message.replace("\r", "")
			lines = stripCarriages.split("\n")
			message = ""

			for line in lines:
				# Double / always returns a floored result (int, not float). 8 / 2 = 4.0, 8 // 2 = 4...
				message = message + line[0:self.displayWidth // 2] + "\n\r" + line[self.displayWidth // 2:self.displayWidth]

		message = self.replaceCustomCharacters(message)

		self.lcd.write_string(message)

	def replaceCustomCharacters(self, message):
		message = message.replace("æ", "\x00")
		message = message.replace("Æ", "\x01")
		message = message.replace("ø", "\x02")
		message = message.replace("Ø", "\x03")
		message = message.replace("å", "\x04")
		message = message.replace("Å", "\x05")
		message = message.replace("g", "\x06")
		return message

	def writeToSimulatedScreen(self, message):
		# Split message up into an array of lines
		printMessage = message.replace("\r", "")
		lines = printMessage.split("\n")
		
		# Add new lines until i matches the display's height
		while True:
			if len(lines) < self.displayHeight:
				lines.append("")
			else:
				break

		paddingSize = 6
		borderYStyle = "│"
		borderXStyle = "─"

		# paddingLine is just a line like this:
		# |                       |
		paddingLine = borderYStyle
		top = "┌"
		bottom = "└"

		# Left border + padding + displayWidth + padding + right border
		for i in range(paddingSize + self.displayWidth + paddingSize):
			top = top + borderXStyle
			bottom = bottom + borderXStyle
			paddingLine = paddingLine + " "

		top = top + "┐"
		bottom = bottom + "┘"
		paddingLine = paddingLine + borderYStyle

		# Make the left and right paddings
		padding = ""
		for i in range(paddingSize):
			padding = padding + " "

		content = ""
		for i in range(len(lines)):
			line = lines[i]
			# Add n spaces to the end of the message, where n = the number of character spaces left on the
			# simulated screen.
			for j in range(self.displayWidth - len(line)):
				line = line + " "
			
			content = 	content + \
						borderYStyle + padding + line + padding + borderYStyle
			
			if i != len(lines) - 1:
				content = content + "\n"

		print(
			top + "\n" +
			paddingLine + "\n" +
			content + "\n" +
			paddingLine + "\n" +
			bottom
		)
		return
