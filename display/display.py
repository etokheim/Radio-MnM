from config import config

if config.raspberry == True:
	from RPi import GPIO
else:
	from EmulatorGUI.EmulatorGUI import GPIO

def write(message):
	if config.debug:
		# Simulate display
		# TODO: Clean this up
		displayWidth = 16

		# Remove new lines and carriage returns
		printMessage = message.replace("\r", "")
		printMessage = printMessage.split("\n")

		firstLineLength = len(printMessage[0])
		firstLine = "│      " + printMessage[0]

		# Add n spaces to the end of the message, where n = the number of character spaces left on the
		# simulated screen.
		for i in range(displayWidth - firstLineLength):
			firstLine = firstLine + " "
		
		# Then add some padding plus the display edge.
		firstLine = firstLine + "      │"

		# Do the same for the second line
		secondLine = "│                            │"

		if len(printMessage) > 1:
			secondLineLength = len(printMessage[1])
			secondLine = "│      " + printMessage[1]
		
			for i in range(displayWidth - secondLineLength):
				secondLine = secondLine + " "
			
			secondLine = secondLine + "      │"

		print("┌────────────────────────────┐")
		print("│                            │")
		print  (         firstLine          )
		print  (         secondLine         )
		print("│                            │")
		print("└────────────────────────────┘")
	
	clear()
	
	if config.raspberry:
		lcd.write_string(message)

def clear():
	if config.raspberry == False:
		print("Clearing display")
	
	if config.raspberry:
		lcd.clear()

if config.raspberry:
	# We are using the GPIO numbering scheme
	lcd = CharLCD(cols=16,
				rows=2,
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
