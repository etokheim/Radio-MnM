from RPLCD.gpio import CharLCD
from RPi import GPIO

# TODO: get debug value from a central place
debug = True

def write(message):
	global lcd, debug

	if debug:
		print(message)
	
	lcd.clear()
	lcd.write_string(message)

def clear():
	lcd.clear()

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
