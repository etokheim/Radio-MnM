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
	formatter = logging.Formatter("%(levelname)s	│ %(message)s")

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
	formatter = logging.Formatter("%(asctime)s - %(levelname)s	│ %(message)s")

	rotateHandler.setFormatter(formatter)
	logger.setLevel(productionLogLevel)
	
	logger.addHandler(rotateHandler)

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
	
	logging.info("Closing database connections")
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
	logger.info("Starting up")
	import app

	# loop = asyncio.get_event_loop()
	# loop.create_task(isLoopRunning())

	# TODO: Maybe it would be an advantage to be able to start and stop the radio from here?
	# app.run()

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	# May want to catch other signals too
	# signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
	# for signal in signals:
	# 	loop.add_signal_handler(
	# 		signal, lambda signal=signal: asyncio.create_task(shutdown(loop, signal=signal)))
	
	# loop.set_exception_handler(handleException)

	try:
		# 
		loop.create_task(main())
		loop.run_forever()
		# asyncio.run(main())
	except Exception as exception:
		# exception = sys.exc_info()[0]
		print("-----------e")
		logger.error(exception)
	finally:
		loop.close()
		logger.info("Successfully shut down the radio")