import datetime
from RPLCD.gpio import CharLCD
from RPi import GPIO
import time
import vlc
from datetime import datetime
import threading
import zope.event

# GPIO.cleanup()

playingChannel = 0
channels = ["http://lyd.nrk.no/nrk_radio_p1_ostlandssendingen_mp3_m", "http://lyd.nrk.no/nrk_radio_alltid_nyheter_mp3_m", "http://lyd.nrk.no/nrk_radio_jazz_mp3_m"]
channelNames = ["NRK P1", "NRK P2", "NRK P3"]
longClickThreshold = 1500
button1DownStart = 0
GPIO.setmode(GPIO.BCM)

# Non-blocking interval execution
import threading

class ThreadJob(threading.Thread):
    def __init__(self,callback,event,interval):
        '''runs the callback function after interval seconds

        :param callback:  callback function to invoke
        :param event: external event for controlling the update operation
        :param interval: time in seconds after which are required to fire the callback
        :type callback: function
        :type interval: int
        '''
        self.callback = callback
        self.event = event
        self.interval = interval
        super(ThreadJob,self).__init__()

    def run(self):
        while not self.event.wait(self.interval):
            self.callback()



event = threading.Event()



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

lcd.write_string(channelNames[playingChannel])

player = vlc.MediaPlayer(channels[playingChannel])
player.play()

#####

time.sleep(5)
player.stop()
player = vlc.MediaPlayer(channels[2])
player.play()

##############

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

pushing = False
pushStart = 0



# I really have no idea how Zope events works, but this project is a very "learn
# as we go" project. Anyways, what I wanted to do here was to create an event system
# where I could subscribe to several events: click, down, up, longClick. This I
# figured out, but I'm still unable to pass arguments down to the event handlers.
# But as I don't need to pass down arguments yet, It's not a big problem yet. An
# example of arguments could be an event for clicking the mouse. That should resolve
# in an event, click, with arguments like pointer position x and y.
import zope.event.classhandler
# import zope.event

class button1Click(object):
    def __repr__(self):
        return self.__class__.__name__

# Skips to the next channel. If you are on the last channel
# skip to the first instead.
# Event is set to the the event which calls it. In this function's case it should be
# set to "click".
def nextChannel(event):
    print("nextChannel %r" % event)

    # Using global variables outside of necessity is usually frowned upon by Python developers
    global playingChannel, channels, player

    lcd.clear()

    if playingChannel + 1 > len(channels) - 1:
        playingChannel = 0

    else:
        playingChannel = playingChannel + 1

    print("Next channel is" + str(playingChannel))

    player.stop()
    player = vlc.MediaPlayer(channels[playingChannel])
    player.play()

    print("Channel " + str(playingChannel) + " (" + channels[playingChannel] + ")")
    lcd.write_string(channelNames[playingChannel])



class button1Down(object):
    def __repr__(self):
        return self.__class__.__name__

def button1DownHandler(event):
    global button1DownStart

    button1DownStart = int(round(time.time() * 1000))

    print("button1DownHandler %r" % event)




class button1Up(object):
    def __repr__(self):
        return self.__class__.__name__

def button1UpHandler(event):
    global button1DownStart
    
    print("button1UpHandler %r" % event)

    button1DownStart = 0




# import zope.event.classhandler
# import zope.event

class button1LongPress(object):
    def __repr__(self):
        return self.__class__.__name__

def button1LongPressHandler(event):
    global longClickThreshold
    
    print("button1LongPressHandler %r" % event)


zope.event.classhandler.handler(button1LongPress, button1LongPressHandler)
zope.event.classhandler.handler(button1Up, button1UpHandler)
zope.event.classhandler.handler(button1Down, button1DownHandler)
zope.event.classhandler.handler(button1Click, nextChannel)



def logButtonState():
    print(pushing)

# interval = ThreadJob(logButtonState,event,0.5)
# interval.start()

while True:
    global pushing, pushStart

    input_state = GPIO.input(18)

    if input_state == True and pushing == True:
        pushing = False

    # If pushing
    if input_state == False and pushStart == 0:
        pushStart = int(round(time.time() * 1000))
        pushing = True
        zope.event.notify(button1Down())

    elif pushStart != 0 and pushing == False:
        now = int(round(time.time() * 1000))
        holdTime = now - pushStart

        zope.event.notify(button1Up())
        # print("Held the button for " + str(holdTime) + " (" + str(now) + " - " + str(pushStart) + ")")
        if holdTime >= longClickThreshold:
            zope.event.notify(button1LongPress())
        else:
            zope.event.notify(button1Click())
        pushStart = 0
