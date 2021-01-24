import tkinter as tk
import logging
import gettext
import time
import threading
from config.config import config
from controls import radio
import os

_ = config["getLanguage"].gettext
logger = logging.getLogger("Radio_mnm")

class Button(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)

		self.state = "released"

		self.pushing = False
		self.pushStart = 0
		self.downStart = 0
		self.sentLongPressEvent = False
		self.sentVeryLongPressEvent = False

		self.press = []
		self.release = []
		self.click = []
		self.longPress = []
		self.longClick = []
		self.veryLongPress = []

		# Timer fireing after starting press. If button's still pressed, it triggers a longPress event
		self.longPressTimer = None

		# Handle high DPI displays
		if os.name == "nt":
			import ctypes
			ctypes.windll.shcore.SetProcessDpiAwareness(1)
		
		self.start()
			
	# Loops through the callbacks parameter (array) and executes them
	def dispatch(self, callbacks):
		for callback in callbacks:
			if callback:
				callback()

	def addEventListener(self, type, callback):
		if type == "press":
			self.press.append(callback)
		elif type == "release":
			self.release.append(callback)
		elif type == "click":
			self.click.append(callback)
		elif type == "longPress":
			self.longPress.append(callback)
		elif type == "longClick":
			self.longClick.append(callback)
		elif type == "veryLongPress":
			self.veryLongPress.append(callback)
		else:
			raise Exception("Event type " + str(callback) + "is not supported.")

	def handlePress(self, arg):
		self.pressedTime = int(time.time() * 1000)
		self.dispatch(self.press)
		
		# Start a timer. If user is still pressing the button when the timer is finished,
		# dispatch a longPress
		self.longPressTimer = threading.Timer(config["longPressThreshold"] / 1000, lambda: self.handleLongPress())
		self.longPressTimer.start()
		
		# Start a timer. If user is still pressing the button when the timer is finished,
		# dispatch a veryLongPress
		self.veryLongPressTimer = threading.Timer(config["veryLongPressThreshold"] / 1000, lambda: self.handleVeryLongPress())
		self.veryLongPressTimer.start()

	def handleRelease(self, arg):
		self.dispatch(self.release)

		# If the user released the button before the timer fired, cancel it
		if self.longPressTimer:
			self.longPressTimer.cancel()
			self.longPressTimer = None
	
		# If the user released the button before the timer fired, cancel it
		if self.veryLongPressTimer:
			self.veryLongPressTimer.cancel()
			self.veryLongPressTimer = None
	
		if int(time.time() * 1000) - self.pressedTime >= config["longClickThreshold"]:
			self.dispatch(self.longClick)
		else:
			self.dispatch(self.click)

	def handleLongPress(self):
		self.longPressTimer = None
		self.dispatch(self.longPress)

	def handleVeryLongPress(self):
		self.veryLongPressTimer = None
		self.dispatch(self.veryLongPress)

	def run(self):
		self.root = tk.Tk()
		self.root.wm_title("Emulated button")
		self.root.protocol("WM_DELETE_WINDOW", self.closeWindow)

		button = tk.Button(self.root, text="Navigation button")
		button.bind("<ButtonPress>", self.handlePress)
		button.bind("<ButtonRelease>", self.handleRelease)
		button.pack(side = tk.TOP, pady = 10)

		label = tk.Label(self.root, text ="Click button to navigate") 
		label.pack(side = tk.TOP, pady = 10)

		self.root.geometry("300x200+100+100")
	   
		self.root.mainloop()


	def closeWindow(self):
		print("Closing window")
		self.root.quit()

	def stop(self):
		self.running = False
		logger.warning("Stopped listening to button with GPIO " + str(self.gpioPin))

	def pause(self):
		self.pauseEvent.clear()
		logger.debug("Paused listening to button with GPIO " + str(self.gpioPin))

	def resume(self):
		self.pauseEvent.set()
		logger.debug("Resumed listening to button with GPIO " + str(self.gpioPin))
