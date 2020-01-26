import datetime
from RPLCD.gpio import CharLCD
from RPi import GPIO
import time

GPIO.setmode(GPIO.BCM)

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

lcd.write_string('Radio M&M')

time.sleep(1.5)

lcd.clear()
GPIO.cleanup()
