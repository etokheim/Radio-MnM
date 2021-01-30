import logging
logger = logging.getLogger("Radio_mnm")
from config.config import config
import threading
import time
import gettext
import sys
from helpers import helpers
from RPi import GPIO

_ = config["getLanguage"].gettext
GPIO.setmode(GPIO.BCM)

from RPLCD.gpio import CharLCD

class Display(threading.Thread):
	def __init__(self, radio, setup):
		threading.Thread.__init__(self)

		self.setup = setup

		if setup["type"] != "Character LCD":
			raise Exception("Invalid display type: " + setup["type"] + ". Check your config.yml")

		self.notificationMessage = ""
		self.clearNotificationTimer = None
		self.standardContent = ""
		self.notificationExpireTime = False
		self.running = True
		# When paused is set, the thread will run, when it's not set, the thread will wait
		self.pauseEvent = threading.Event()
		self.currentlyDisplayingMessage = ""
		self.lastWriteTime = 0
		self.writeQueue = []
		self.writeQueueTimer = None
		self.writeDelay = setup["writeDelay"]

		# For how many steps we should pause when displaying the start of the line (1 step = displayScrollSpeed)
		self.displayScrollingStartPauseSteps = 12

		# For how many steps we should pause when displaying the end of the line (1 step = displayScrollSpeed)
		self.displayScrollingStopPauseSteps = 8

		# Time between scrolls
		self.displayScrollSpeed = 0.2 # seconds
		
		self.scrollOffset = 0 - self.displayScrollingStartPauseSteps
		self.lastDisplayedMessage = ""
		self.lastDisplayedCroppedMessage = ""

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

		# Turn off the backlight
		self.lcd.backlight_enabled = False

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

		self.start()

	def run(self):
		while self.running:
			# Take a short nap between scrolls.
			# It's better to sleep right before the pause event, so the content doesn't linger if the thread
			# is paused.
			time.sleep(self.displayScrollSpeed)

			# Wait, if the thread is set on hold
			self.pauseEvent.wait()

			###################
			# Make it scroll! #
			###################
			stripCarriages = self.currentlyDisplayingMessage.replace("\r", "")
			lines = stripCarriages.split("\n")

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

	def stopScrollThread(self):
		self.clear()
		self.running = False
		logger.warning("Stopped display")

	def stopScrolling(self):
		self.clear()
		self.pauseEvent.clear()
		logger.debug("Stopped scrolling loop")

	def resumeScrolling(self):
		self.pauseEvent.set()
		logger.debug("Resumed scrolling loop")

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
			
			compat_mode = self.setup["lcdCompatibilityMode"],
			
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

	# Writes standard content to the display. If it overflows, it also starts the scrolling thread, which
	# makes the content scroll automatically.
	def writeStandardContent(self, standardContent = None):
		# Set default value to standardContent (can't refer to self while setting default values)
		if standardContent is None:
			standardContent = self.standardContent

		# Put the standard content into a variable accessible from the scrolling thread
		self.standardContent = standardContent

		if not self.notificationMessage:
			self.writeAndScrollIfOverflowing(standardContent)

	def writeAndScrollIfOverflowing(self, content):
		# Check if content will overflow
		stripCarriages = content.replace("\r", "")
		lines = stripCarriages.split("\n")
		overflowingContent = False
		croppedContent = ""

		index = 0
		for line in lines:
			# Crop the lines, so we can write it directly
			croppedContent = croppedContent + line[0:16]
			
			if index != len(line) - 1:
				croppedContent = croppedContent + "\r\n"

			# Check if content will overflow
			if len(line) > self.displayWidth:
				overflowingContent = True
			
			index = index + 1

		# Write content to the screen at once (as the scrolling thread can be in the middle of a sleep. Also
		# if the content doesn't overflow, we have to write it manually).
		self.write(croppedContent)
		self.currentlyDisplayingMessage = content

		# If overflowing content, start the scroller thread
		if overflowingContent:
			self.resumeScrolling()
		else:
			if self.pauseEvent.is_set():
				self.stopScrolling()

	# A notification has a limited lifespan. It is displayed for a set duration in seconds (defaults to 2).
	# When a notification expires, the standard content is displayed. Standard content is what's playing etc.
	def notification(self, message, duration = 2):
		self.notificationMessage = message
		self.writeAndScrollIfOverflowing(message)

		# Stop the timer for clearing notifications if it's already running
		if self.clearNotificationTimer:
			self.clearNotificationTimer.cancel()
			self.clearNotificationTimer = None

		# Start a timer to clear the notification after the duration has expired
		self.clearNotificationTimer = threading.Timer(duration, self.clearNotification)
		self.clearNotificationTimer.start()

	def clearNotification(self):
		self.notificationMessage = None
		self.clearNotificationTimer = None

		# After clearing the notification, display the standard content immediately
		self.writeStandardContent()

	# Clears the display
	def clear(self):
		self.lcd.clear()

	def write(self, message):
		# The display can be None if it's in the middle of a reinitialization
		if not self.lcd:
			logger.error("Couldn't write to the display as the lcd was None")
			return

		# Check whether the display is ready for new text. If not, we'll add the message to the write queue.
		if int(time.time() * 1000) - self.lastWriteTime < self.writeDelay:
			self.writeQueue.append(message)
			logger.debug("The display was not ready to write. The message was delayed")

		# Else the display is ready, and we can write
		else:
			self.lastWriteTime = int(time.time() * 1000)
			self.clear()
			
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

		# Check if there's anything in the write queue.
		# If there is, start a timer to write it.
		if len(self.writeQueue):
			if not self.writeQueueTimer:
				self.writeQueueTimer = threading.Timer(self.writeDelay / 1000, lambda: self.writeFromQueue())
				self.writeQueueTimer.start()


	def writeFromQueue(self):
		self.writeQueueTimer.cancel()
		self.writeQueueTimer = None

		message = self.writeQueue[0]
		self.writeQueue.pop(0)
		self.write(message)


	def replaceCustomCharacters(self, message):
		message = message.replace("æ", "\x00")
		message = message.replace("Æ", "\x01")
		message = message.replace("ø", "\x02")
		message = message.replace("Ø", "\x03")
		message = message.replace("å", "\x04")
		message = message.replace("Å", "\x05")
		message = message.replace("g", "\x06")
		return message

	def turnOffBacklight(self):
		self.lcd.backlight_enabled = False