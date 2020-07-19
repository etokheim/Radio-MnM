import logging
logger = logging.getLogger("Radio_mnm")
from config import config
import threading
import time
import gettext
import sys
from helpers import helpers
import os

_ = config.nno.gettext

if config.raspberry == True:
	from RPi import GPIO
	from RPLCD.gpio import CharLCD
else:
	from EmulatorGUI.EmulatorGUI import GPIO

def initializeLcd():
	return CharLCD(
		# (int) Number of columns per row (usually 16 or 20). Default: 20.
		cols=actualDisplayWidth,
		
		# (int) Number of display rows (usually 1, 2 or 4). Default: 4.
		rows=actualDisplayHeight,
		
		pin_rs=int(os.environ["mnm_lcdRsToGpio"]),
		
		pin_e=int(os.environ["mnm_lcdEnToGpio"]),
		
		pins_data=[int(os.environ["mnm_lcdData4ToGpio"]), int(os.environ["mnm_lcdData5ToGpio"]), int(os.environ["mnm_lcdData6ToGpio"]), int(os.environ["mnm_lcdData7ToGpio"])],
		
		numbering_mode=GPIO.BCM,
		
		compat_mode = helpers.castToBool(os.environ["mnm_lcdCompatibleMode"]),
		
		# (int) Some 1 line displays allow a font height of 10px. Allowed: 8 or 10.
		dotsize = int(os.environ["mnm_lcdDotSize"]),
		
		# The character map used. Depends on your LCD. This must be either A00 or A02 or ST0B.
		charmap = os.environ["mnm_lcdCharMap"],
		
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
	)

if config.raspberry:
	# Compensate for a weird display quirk. Read more in the comments above
	if helpers.castToBool(os.environ["mnm_oneDisplayLineIsTwoLines"]):
		actualDisplayWidth = int(os.environ["mnm_displayWidth"]) // 2
		actualDisplayHeight = int(os.environ["mnm_displayHeight"]) * 2
	else:
		actualDisplayWidth = int(os.environ["mnm_displayWidth"])
		actualDisplayHeight = int(os.environ["mnm_displayHeight"])

	# We are using the GPIO numbering scheme
	lcd = initializeLcd()

class Display(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
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
		self.virtualDisplay = helpers.castToBool(os.environ["mnm_virtualDisplay"])

		# Amount of characters, not pixels
		self.displayWidth = int(os.environ["mnm_displayWidth"])
		self.displayHeight = int(os.environ["mnm_displayHeight"])

		# Weird display quirk, where one line is two lines for the computer. I guess this is due to
		# some cost saving initiative in display production.
		self.oneDisplayLineIsTwoLines = helpers.castToBool(os.environ["mnm_oneDisplayLineIsTwoLines"])

		# Custom characters
		self.ae = (
			0b00000,
			0b01011,
			0b10101,
			0b10111,
			0b10100,
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

		lcd.create_char(0, self.ae)
		lcd.create_char(1, self.AE)
		lcd.create_char(2, self.oe)
		lcd.create_char(3, self.OE)
		lcd.create_char(4, self.aa)
		lcd.create_char(5, self.AA)


	def run(self):
		# Wait, if the thread is set on hold
		self.pauseEvent.wait()
		
		while self.running:
			# Wait, if the thread is set on hold
			self.pauseEvent.wait()

			# Set standard content if radio is on
			if config.radio.on:
				# Set standard content
				# Selected channel can be None when the radio is on, only right after a reset.
				if config.radio.selectedChannel is not None:

					# Format standard content based on screen size
					# Set the second line's content:
					if self.displayHeight >= 2:
						# By default, display the meta (ie. [Song] - [Artist])
						secondLine = config.radio.media.get_meta(12)
						
						# Get the radio's state
						state = str(config.radio.getState())

						# Display any channel errors
						if config.radio.channelError:
							secondLine = config.radio.channelError

						# Display any special states
						elif state != "State.Playing" and state != "State.NothingSpecial":
							secondLine = config.radio.getStateText()

						# Meta can be None for a second after the channel starts playing (or if it's actually empty)
						elif secondLine is None:
							secondLine = ""

						self.standardContent = config.radio.selectedChannel["name"] + "\n\r" + str(secondLine)
					else:
						self.standardContent = config.radio.selectedChannel["name"]
				elif self.standardContent == "":
					self.standardContent = "No channels"

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

			time.sleep(self.displayScrollSpeed)

	def stop(self):
		self.clear()
		self.running = False
		logger.warning("Stopped display")

	def pause(self):
		self.clear()
		lcd = None
		lcd = initializeLcd()
		self.pauseEvent.clear()
		logger.debug("Paused display handling loop")

	def resume(self):
		self.pauseEvent.set()
		# \n for new line \r for moving to the beginning of current line
		config.radio.display.notification(">- RADIO M&M  -<\n\r" + _("Got ") + str(len(config.radio.channels)) + _(" channels"), 3)
		logger.debug("Resumed display handling loop")

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
		
		if config.raspberry:
			lcd.clear()

	def displayMessage(self, messageType="notification"):
		stripCarriages = self.currentlyDisplayingMessage.replace("\r", "")
		lines = stripCarriages.split("\n")

		# If there is a new text to display
		if self.lastDisplayedMessage != self.currentlyDisplayingMessage:
			# Reset the text offset (scroll position)
			self.scrollOffset = 0 - self.displayScrollingStartPauseSteps
			
			# Only do this if displaying channel info
			if messageType == "channelInfo" and self.displayHeight >= 2:
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
		
		# Write message to the actual display, if we are running on a Raspberry Pi
		if config.raspberry:
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

			lcd.write_string(message)

	def replaceCustomCharacters(self, message):
		message = message.replace("æ", "\x00")
		message = message.replace("Æ", "\x01")
		message = message.replace("ø", "\x02")
		message = message.replace("Ø", "\x03")
		message = message.replace("å", "\x04")
		message = message.replace("Å", "\x05")
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
