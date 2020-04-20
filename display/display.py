from config import config

if config.raspberry == True:
	from RPi import GPIO
else:
	from EmulatorGUI.EmulatorGUI import GPIO

def write(message):
	if config.debug:
		print(message)
	
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
