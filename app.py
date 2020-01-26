import datetime
from RPLCD.gpio import CharLCD
from RPi import GPIO
import time
import vlc

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

lcd.clear()

lcd.write_string('Radio M&M')

time.sleep(1.5)
lcd.clear()

lcd.write_string('Fetching audio streams')

time.sleep(1)
lcd.clear()

lcd.write_string('Got 3 streams')

time.sleep(1)
lcd.clear()


playingChannel = 0
channels = ["http://lyd.nrk.no/nrk_radio_p1_ostlandssendingen_mp3_m", "http://lyd.nrk.no/nrk_radio_alltid_nyheter_mp3_m", "http://lyd.nrk.no/nrk_radio_jazz_mp3_m"]
channelNames = ["NRK P1", "NRK P2", "NRK P3"]

lcd.write_string(channelNames[playingChannel])

player = vlc.MediaPlayer(channels[playingChannel])
player.play()

# time.sleep(5)
# player.stop()
# player = vlc.MediaPlayer(channels[2])
# player.play()

#GPIO.cleanup()
###############

GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
    input_state = GPIO.input(18)
    if input_state == False:
        lcd.clear()
        playingChannel = playingChannel + 1

        player.stop()
        player = vlc.MediaPlayer(channels[playingChannel])
        player.play()

        print("Channel " + str(playingChannel) + " (" + channels[playingChannel] + ")")
        lcd.write_string(channelNames[playingChannel])
        time.sleep(0.2)
