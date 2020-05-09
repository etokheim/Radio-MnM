#!/bin/bash

######################################
#                                    #
#               Setup                #
#                                    #
######################################
# Exit if any command fails
set -e

# Check if sudo
if [ `whoami` != root ]
	then echo "Please run as sudo"
	exit
fi

development=false
if [ $1 == "--development" ]; then
	development=true
fi

scriptLocation="$(dirname $(readlink -f "$0"))"

# Just removes the last directory from the scriptLocation
appLocation="$(echo $scriptLocation | sed 's,/*[^/]\+/*$,,')"

currentStep=1
function step() {
	if [ $2 ]; then
		newLine=false
	else
		newLine=true
	fi
	
	if [ $newLine = true ]; then
		# Underlined, light gray
		echo -e "\n\e[94mStep $currentStep - $1\e[0m\n\n"
	else
		# Underlined, light gray
		# Don't create newline
		echo -en "\n\e[94mStep $currentStep - $1\e[0m"
	fi

	currentStep=$((currentStep+1))
}


######################################
#                                    #
#        Install dependencies        #
#                                    #
######################################
step "Update"
apt-get update -y

# Only upgrade if we are in a production environment
# Dev users might not appreciate an auto upgrade.
if [ $development = false ]; then
	apt-get upgrade -y
fi

step "Install dependencies"
apt-get install -y \
	vlc \
	pulseaudio \
	python3 \
	python3-pip \
	nano \
	git

step "Install Python dependencies"
pip3 install -r "$scriptLocation/../requirements.txt"

if [ $development = true ]; then
	apt-get install -y gettext
fi


######################################
#                                    #
#    Fixing file permissions and     #
# creating missing files and folders #
#                                    #
######################################
step "Updating file permissions and creating necessary folders..." true


# Make db and logs directories or the script will error out
if [ ! -d "$scriptLocation/../db" ]; then
	mkdir "$scriptLocation/../db"
fi

if [ ! -d "$scriptLocation/../logs" ]; then
	mkdir "$scriptLocation/../logs"
fi

# If we are in a production environment
if [ $development = false ]; then
	# Create a radio-mnm user with as few as possible permissions and let it run the app
	if ! id "radio-mnm" >/dev/null 2>&1; then
		useradd -m radio-mnm

		# Grant access to GPIO pins
		adduser radio-mnm gpio
		
		# Grant access to play audio
		adduser radio-mnm audio
	fi
	
	# Give all the files to radio-mnm
	chown radio-mnm "$appLocation" -R
	chmod 774 . -R
fi

# Making the rest of the script files executable
chmod +x "$appLocation/load-dotenv.sh" "$scriptLocation/update.sh" "$scriptLocation/locales_apply_update.sh" "$scriptLocation/locales_update.sh"

echo -e "\t\e[32mDone!\e[0m\n\n"


######################################
#                                    #
#         Register service           #
#                                    #
######################################
serviceFile=\
"[Unit]
Description=Radio M&M
After=network.target

[Service]
ExecStart=/usr/bin/python3 -u -m radio_mnm
WorkingDirectory=$appLocation
StandardOutput=inherit
StandardError=inherit
Restart=always
User=radio-mnm
EnvironmentFile=$appLocation/.env

[Install]
WantedBy=multi-user.target"

if [ $development = true ]; then
	echo -e "\nDev environment is ready. You can start the app by running the following command:"
	echo -e "\tpython3 -m radio_mnm"
else
	step "Registering service..." true
	
	# First create the service file. This file will belong to root, as we are running as
	# sudo, but we can't do anything about it as we don't know who the normal user is.
	# Therefor we will give free access to this file afterwards.
	echo "$serviceFile" > "$scriptLocation/radio-mnm.service"

	# Give everyone access to the file, as we don't know which user to give it to.
	chmod 666 "$scriptLocation/radio-mnm.service"

	# Then copy it into the correct location and give it stricter permissions.
	cp "$scriptLocation/radio-mnm.service" "/etc/systemd/system"
	chown root:root "/etc/systemd/system/radio-mnm.service"
	chmod 644 "/etc/systemd/system/radio-mnm.service"

	# Reload daemon (necessary if a radio-mnm.service has already been registered).
	sudo systemctl daemon-reload

	# Start the service
	sudo systemctl start radio-mnm.service

	# Start the service on boot
	sudo systemctl enable radio-mnm.service

	echo -e "\t\t\t\t\t\t\e[32mDone!\e[0m\n\n"

	echo -e "\nThe service is running successfully and starts automatically on boot"
fi