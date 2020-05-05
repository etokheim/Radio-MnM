import logging
logger = logging.getLogger("Radio_mnm")
from config import config
import threading
import time
import gettext

_ = config.nno.gettext

if config.raspberry == True:
	from RPi import GPIO
	from RPLCD.gpio import CharLCD
else:
	from EmulatorGUI.EmulatorGUI import GPIO


if config.raspberry:
	# We are using the GPIO numbering scheme
	lcd = CharLCD(
		# (int) Number of columns per row (usually 16 or 20). Default: 20.
		cols=config.displayWidth,
		
		# (int) Number of display rows (usually 1, 2 or 4). Default: 4.
		rows=config.displayHeight,
		
		pin_rs=26,
		
		pin_e=19,
		
		pins_data=[13, 6, 5, 11],
		
		numbering_mode=GPIO.BCM,
		
		compat_mode = True,
		
		# (int) Some 1 line displays allow a font height of 10px. Allowed: 8 or 10.
		dotsize = 8,
		
		# The character map used. Depends on your LCD. This must be either A00 or A02 or ST0B.
		charmap = 'A00',
		
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
		
		self.scrollOffset = 0 - config.displayScrollingStartPauseSteps
		self.lastDisplayedMessage = ""
		self.lastDisplayedCroppedMessage = ""

	def run(self):
		# Wait, if the thread is set on hold
		self.pauseEvent.wait()
		
		while self.running:
			# Wait, if the thread is set on hold
			self.pauseEvent.wait()

			# Set standard content if radio is on
			if config.on:
				# meta can be None for a second after the channel starts playing (or if it's actually empty)
				meta = config.radio.media.get_meta(12)
				if meta is None:
					meta = ""
				
				# Set standard content
				# Selected channel can be None when the radio is on, only right after a reset.
				if config.radio.selectedChannel is not None:
					# Format standard content based on screen size
					if config.displayHeight >= 2:
						self.standardContent = config.radio.selectedChannel["name"] + "\n\r" + str(meta)
					else:
						self.standardContent = config.radio.selectedChannel["name"]
				else:
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

			time.sleep(config.displayScrollSpeed)

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
		# \n for new line \r for moving to the beginning of current line
		display.notification(">- RADIO M&M -<\n\r" + _("Got ") + str(len(config.radio.channels)) + _(" channels"), 4)
		logger.debug("Resumed display handling loop")

	# A notification has a limited lifespan. It is displayed for a set duration in seconds (defaults to 2).
	# When a notification expires, the standard content is displayed. Standard content is what's playing etc.
	def notification(self, message, duration = 2):
		self.notificationMessage = message
		self.notificationExpireTime = int(round(time.time() * 1000)) + duration * 1000

		self.write(message)

	# Clears the display
	def clear(self):
		if config.debug:
			print("│ - -  Display cleared   - - │")
		
		if config.raspberry:
			lcd.clear()

	def displayMessage(self, messageType="notification"):
		stripCarriages = self.currentlyDisplayingMessage.replace("\r", "")
		lines = stripCarriages.split("\n")

		# If there is a new text to display
		if self.lastDisplayedMessage != self.currentlyDisplayingMessage:
			# Reset the text offset (scroll position)
			self.scrollOffset = 0 - config.displayScrollingStartPauseSteps
			
			# Only do this if displaying channel info
			if messageType == "channelInfo" and config.displayHeight >= 2:
				# When the text changes, "clear the second line" for å brief moment, so the user
				# more easily can understand that a new text was inserted.
				# Crap, this only works for channels, but notifications are also parsed through here...
				self.write(lines[0])

			time.sleep(0.25)
			
		composedMessage = ""
		croppedLines = []
		longestLineLength = 0
		displayWidth = config.displayWidth

		loopTimes = len(lines)
		if loopTimes > config.displayHeight:
			loopTimes = config.displayHeight

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
		self.clear()

		# Simulate a display in the terminal, if we are running in debug mode
		# Do not directly use this function to write to the display. Use notification()
		if config.debug:
			self.writeToSimulatedScreen(message)
		
		# Write to the actual display, if we are running on a Raspberry Pi
		if config.raspberry:
			lcd.write_string(message)

	def writeToSimulatedScreen(self, message):
		# Split message up into an array of lines
		printMessage = message.replace("\r", "")
		lines = printMessage.split("\n")
		
		# Add new lines until i matches the display's height
		while True:
			if len(lines) < config.displayHeight:
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
		for i in range(paddingSize + config.displayWidth + paddingSize):
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
			for j in range(config.displayWidth - len(line)):
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

display = Display()