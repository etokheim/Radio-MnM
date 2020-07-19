# Boolean environment variables has to be casted to Python booleans as they are only parsed
# as strings. A string will always evaluate to true.
def castToBool(string):
	if string == "True" or string == "true" or string == "1":
		return True
	else:
		return False