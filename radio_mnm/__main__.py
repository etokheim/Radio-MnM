import sys
sys.path.append("radio_mnm/")

# The log setup must be done before importing everything else, as some of the other modules also
# use the logging module. However, I think this only was a problem while we were using the root
# logger. We have now switched to a separate logger "Radio_mnm".
import logging
from logging.handlers import RotatingFileHandler
from config.config import config
import asyncio
import signal
import aiohttp
import os

# Set log level
level = config["productionLogLevel"]
if level == "critical":
	productionLogLevel = logging.CRITICAL
elif level == "error":
	productionLogLevel = logging.ERROR
elif level == "warning":
	productionLogLevel = logging.WARNING
elif level == "warn":
	productionLogLevel = logging.WARNING
elif level == "info":
	productionLogLevel = logging.INFO
elif level == "debug":
	productionLogLevel = logging.DEBUG
else:
	productionLogLevel = logging.INFO

# Create a new logger
logger = logging.getLogger("Radio_mnm")

if config["debug"]:
	# Console handler
	streamHandler = logging.StreamHandler()

	# If we later want to include logger name: " - %(name)s"
	formatter = logging.Formatter("%(levelname)s	| %(message)s")

	streamHandler.setFormatter(formatter)
	logger.setLevel(logging.DEBUG)
	
	logger.addHandler(streamHandler)
else:
	logFile = "logs/radio_mnm.log"
	rotateHandler = RotatingFileHandler(
		logFile,
		maxBytes=1024 * 1024 * 5, # Mega bytes
		backupCount=5
	)
	
	# If we later want to include logger name: " - %(name)s"
	formatter = logging.Formatter("%(asctime)s - %(levelname)s	| %(message)s")

	rotateHandler.setFormatter(formatter)
	logger.setLevel(productionLogLevel)
	
	logger.addHandler(rotateHandler)

radio = None

async def isLoopRunning():
	print("Is the loop still running?")
	loop = asyncio.get_event_loop()
	print(str(loop))
	await asyncio.sleep(5)
	await isLoopRunning()

def handleException(loop, exception):
	logger.error(exception)
	logger.info("Shutting down due to exception")
	asyncio.create_task(shutdown(loop))

async def shutdown(loop, signal = None):
	if signal:
		logging.info(f"Received exit signal {signal.name}...")
	
	logging.info("Nacking outstanding messages")
	tasks = [t for t in asyncio.all_tasks() if t is not
				asyncio.current_task()]

	[task.cancel() for task in tasks]

	logging.info(f"Cancelling {len(tasks)} outstanding tasks")
	await asyncio.gather(*tasks, return_exceptions=True)
	logging.info(f"Flushing metrics")
	session = aiohttp.ClientSession()
	await session.close()
	loop.stop()

async def main():
	global radio
	loop = asyncio.get_event_loop()

	# Local imports
	from controls import radio

	logger.info("Starting up")
	
	radio = radio.Radio()

	# Couldn't figure out how to put the error handling into the radio class.
	# The problem was getting self into the logCallback function which is decorated
	# by vlc. We need the radio object to get the instance and the handleError function.
	# Temporary put it here. TODO: Fix that.
	import vlc
	import ctypes

	# Load the Windows ctypes library if Windows
	if os.name == "nt":
		libc = ctypes.cdll.msvcrt
	else:
		libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))

	vsnprintf = libc.vsnprintf

	vsnprintf.restype = ctypes.c_int
	vsnprintf.argtypes = (
		ctypes.c_char_p,
		ctypes.c_size_t,
		ctypes.c_char_p,
		ctypes.c_void_p,
	)

	# Catch the VLC logs and output them to our logs aswell
	@vlc.CallbackDecorators.LogCb
	def logCallback(data, level, ctx, fmt, args):
		# Skip if level is lower than error
		# TODO: Try to solve as many warnings as possible
		if level < 4:
			return

		# Format given fmt/args pair
		BUF_LEN = 1024
		outBuf = ctypes.create_string_buffer(BUF_LEN)
		vsnprintf(outBuf, BUF_LEN, fmt, args)

		# Transform to ascii string
		log = outBuf.raw.decode('ascii').strip().strip('\x00')

		# Handle any errors
		if level > 3:
			shouldLog = radio.handleError(log)

			# If noisy error, then don't log it
			if not shouldLog:
				return

		# Output vlc logs to our log
		if level == 5:
			logger.critical(log)
		elif level == 4:
			logger.error(log)
		elif level == 3:
			logger.warning(log)
		elif level == 2:
			logger.info(log)

	radio.instance.log_set(logCallback, None)

	# Create a aiohttp session to be used across the app
	# session = aiohttp.ClientSession(loop=loop)

	# loop.create_task(isLoopRunning())

	# TODO: Maybe it would be an advantage to be able to start and stop the radio from here?
	# app.run()

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.set_debug(enabled=True)
	
	# May want to catch other signals too
	# signals = (
	# 	signal.SIGHUP,		# Hangup detected on controlling terminal or death of controlling process.
	# 	signal.SIGTERM,		# Termination signal.
	# 	signal.SIGINT		# Keyboard interrupt (Signal Interrupt). Default action is to raise KeyboardInterrupt.
	# )

	# for signal in signals:
	# 	loop.add_signal_handler(
	# 		signal, lambda signal=signal: asyncio.create_task(shutdown(loop, signal=signal)))
	
	# loop.set_exception_handler(handleException)

	try:
		# 
		loop.create_task(main())
		loop.run_forever()
		# asyncio.run(main(), debug=True)
	except KeyboardInterrupt:
		logger.warning("Keyboard interrupt detected. Shutting down gracefully.")
	# except Exception as exception:
	# 	# exception = sys.exc_info()[0]
	# 	print("-----------e")
	# 	logger.error(exception)
	finally:
		loop.close()
		logger.info("Successfully shut down the radio")