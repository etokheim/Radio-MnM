# The log setup must be done before importing everything else, as some of the other modules also
# use the logging module. However, I think this only was a problem while we were using the root
# logger. We have now switched to a separate logger "Radio_mnm".
import logging
from logging.handlers import RotatingFileHandler
from config import config

# Create a new logger
logger = logging.getLogger("Radio_mnm")

if config.debug:
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
	logger.setLevel(logging.DEBUG)
	
	logger.addHandler(rotateHandler)

from radio_mnm import app

def main():
	# The logic for starting your application.
	app.run()

if __name__ == "__main__":
	main()