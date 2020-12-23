###################################
#                                 #
#             Config              #
#                                 #
###################################
import gettext
import logging
import yaml

checkButtonStateInterval = 0.01

config = None

with open("config.yml", "r") as stream:
	try:
		config = yaml.safe_load(stream)
	except yaml.YAMLError as exception:
		print(exception)

config["getLanguage"] = gettext.translation("base", localedir="locales", languages=[config["language"]])