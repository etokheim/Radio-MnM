import datetime
from RPLCD.gpio import CharLCD
from RPi import GPIO
import time
import vlc
from datetime import datetime
import threading
import zope.event
# import requests


playingChannel = 0
# Will be populated by an API request
channels = None
longClickThreshold = 1500
button1DownStart = 0
GPIO.setmode(GPIO.BCM)
on = False
player = None

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

def getChannels():
    global channels

    response = requests.get("https://radio.tokheimgrafisk.no/channels")
    response = response.json()
    print(response[0])
    print(response[0]["streams"])
    print(response[0]["name"])

    channels = response

    player = vlc.MediaPlayer(channels[playingChannel]["streams"][0])

getChannels()


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


GPIO.setmode(GPIO.BCM)

# Button 1
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Button 2
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

pushing = False
pushStart = 0

button2Pushing = False



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

# Event is set to the the event which calls it. In this function's case it should be
# set to "click".
def button1ClickHandler(event):
    print("button1Click %r" % event)

    bumpChannel(1)


# Bumps the channel n times. Loops around if bumping past the last channel.
def bumpChannel(channelsToSkip):
    global playingChannel, channels
    bumpTo = playingChannel

    # Make the default be to skip to next channel
    if channelsToSkip is None:
        channelsToSkip = 1

    print("channels:")
    print(channels)
    # Number of channels to skip which remains after removing overflow.
    # (Overflow: if you are playing channel 3 of 10 and is instructed to skip 202 channels ahead,
    # you would end up on channel 205. The overflow is 200, and we should return channel 5 (3 + 2))
    remaining = (len(channels) + channelsToSkip) % len(channels)

    if bumpTo + remaining > len(channels) - 1:
        bumpTo = bumpTo - len(channels) + remaining

    elif bumpTo + remaining < 0:
        bumpTo = len(channels) + bumpTo + remaining

    else:
        bumpTo = bumpTo + remaining

    channel(bumpTo)

    

# Takes the parameter (int) and switches to that channel
def channel(channelNumber):
    global player, on, channels

    if on == False:
        print("Can't switch channel when radio is off!")
        return

    player.stop()
    player = vlc.MediaPlayer(channels[playingChannel]["streams"][0])
    player.play()

    print("Channel " + str(playingChannel) + " (" + channels[playingChannel]["name"] + ")")
    
    lcd.clear()
    
    print(channels[playingChannel]["name"])
    lcd.write_string(channels[playingChannel]["name"])

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


class button2Up(object):
    def __repr__(self):
        return self.__class__.__name__

def button2UpHandler(event):
    global on
    on = False
    print("button2UpHandler %r" % event)
    player.stop()
    lcd.clear()


class button2Down(object):
    def __repr__(self):
        return self.__class__.__name__

def button2DownHandler(event):
    global on, channels
    on = True
    print("button2DownHandler %r" % event)

    lcd.clear()

    player.play()


    print('Radio M&M')
    lcd.write_string('Radio M&M')

    time.sleep(2)
    lcd.clear()

    print('Fetching audio streams')
    lcd.write_string('Fetching audio streams')
    time.sleep(1.5)
    lcd.clear()

    print('Got 3 streams')
    lcd.write_string('Got 3 streams')

    time.sleep(1.5)
    lcd.clear()

    print(channels[playingChannel]["name"])
    lcd.write_string(channels[playingChannel]["name"])




# import zope.event.classhandler
# import zope.event

class button1LongPress(object):
    def __repr__(self):
        return self.__class__.__name__

def button1LongPressHandler(event):
    global longClickThreshold
    
    print("button1LongPressHandler %r" % event)
    bumpChannel(-1)


zope.event.classhandler.handler(button1LongPress, button1LongPressHandler)
zope.event.classhandler.handler(button1Up, button1UpHandler)
zope.event.classhandler.handler(button1Down, button1DownHandler)
zope.event.classhandler.handler(button1Click, button1ClickHandler)
zope.event.classhandler.handler(button2Down, button2DownHandler)
zope.event.classhandler.handler(button2Up, button2UpHandler)



def logButtonState():
    print(button2Pushing)

# interval = ThreadJob(logButtonState,event,0.5)
# interval.start()

while True:
    time.sleep(0.01)

    button1State = GPIO.input(18)
    button2State = GPIO.input(17)

    if button1State == True and pushing == True:
        pushing = False

    # If pushing
    if button1State == False and pushStart == 0:
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

    # If pushing
    if button2State == False:
        if button2Pushing == False:
            # Send wake event
            zope.event.notify(button2Down())

        button2Pushing = True

    else:
        if button2Pushing == True:
            # Send sleep event
            zope.event.notify(button2Up())

        button2Pushing = False
