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

castToBool = helpers.castToBool

###################################
#                                 #
#              Setup              #
#                                 #
###################################
# Language
# TODO: Get language from API
nno = gettext.translation("base", localedir="locales", languages=["nno"])

debug = castToBool(os.environ["mnm_debug"])

# If running on a raspberry pi, set to true
# This is a bit over simplified, but it works (just checks if the machine
# is an arm machine or not).
raspberry = False
if os.uname()[4][:3] == "arm":
	raspberry = True

longPressThreshold = 600
veryLongPressThreshold = 5000

checkPowerSwitchStateInterval = 0.25
checkButtonStateInterval = 0.01

apiServer = os.environ["mnm_apiServer"]
verifyCertificate = True


###################################
#                                 #
#              Radio              #
#                                 #
###################################
# TODO: Move radio out of the config file

# Will be set to the radio 
radio = None
