###################################
#                                 #
#            Overview             #
#                                 #
###################################
# The config file is a nice place to set, transform or parse values in a central place.


###################################

import os
import gettext
import logging
from helpers import helpers
import yaml

castToBool = helpers.castToBool




debug = castToBool(os.environ["mnm_debug"])

# If running on a raspberry pi, set to true
# This is a bit over simplified, but it works (just checks if the machine
# is an arm machine or not).
raspberry = False
if os.uname()[4][:3] == "arm":
	raspberry = True

longPressThreshold = 600
veryLongPressThreshold = 5000

checkButtonStateInterval = 0.01

apiServer = os.environ["mnm_apiServer"]
verifyCertificate = True

config = None

with open("config.yml", "r") as stream:
	try:
		config = yaml.safe_load(stream)
	except yaml.YAMLError as exception:
		print(exception)

config["getLanguage"] = gettext.translation("base", localedir="locales", languages=[config["language"]])

###################################
#                                 #
#              Setup              #
#                                 #
###################################
# Language
# TODO: Get language from API
nno = config["getLanguage"]