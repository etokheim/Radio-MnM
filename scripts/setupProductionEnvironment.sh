#!/bin/bash

#####################################
#                                   #
#               Setup               #
#                                   #
#####################################
# Exit if any command fails
set -e

# Check if sudo
if [ `whoami` != root ]
	then echo "Please run as sudo"
	exit
fi

scriptLocation="$(dirname $(readlink -f "$0"))"

currentStep=1
function step() {
	if [ $2 ]; then
		newLine=false
	else
		newLine=true
	fi
	
	if [ $newLine = true ]; then
		echo -e "\nStep $currentStep - $1\n\n"
	else
		# Don't create newline
		echo -en "\nStep $currentStep - $1"
	fi

	currentStep=$((currentStep+1))
}


#####################################
#                                   #
#        Install dependencies       #
#                                   #
#####################################
step "Update"
apt-get update -y

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


#####################################
#                                   #
# Create missing files and folders  #
#                                   #
#####################################
step "Creating necessary folders..." true

# Make db and logs directories or the script will error out
if [ ! -d "$scriptLocation/../db" ]; then
	mkdir "$scriptLocation/../db"
fi

if [ ! -d "$scriptLocation/../logs" ]; then
	mkdir "$scriptLocation/../logs"
fi

echo -e "\tDone!\n\n"


#####################################
#                                   #
#         Register service          #
#                                   #
#####################################
step "Registering service..." true
cp "$scriptLocation/radio-mnm.service" "/etc/systemd/system"

# Reload daemon (necessary if a radio-mnm.service has already been registered).
sudo systemctl daemon-reload

# Start the service
sudo systemctl start radio-mnm.service

# Start the service on boot
sudo systemctl enable radio-mnm.service

echo -e "\t\tDone!\n\n"

echo -e "\nThe service is running successfully and starts automatically on boot"