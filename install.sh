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

# Just removes the last directory from the scriptLocation
appLocation="$(dirname $(readlink -f "$0"))"

scriptLocation="$appLocation/scripts"

# Let's just guess who the local user is based on who owns the python module folder.
# Note that we are using the group, not the owner, as we edit the owner and this script
# could be run multiple times (even though it's not really necessary).
userName=$(stat -c '%G' $appLocation/radio_mnm)

currentStep=1
function step() {
	if [ $2 ]; then
		newLine=false
	else
		newLine=true
	fi
	
	if [ $newLine = true ]; then
		# Underlined, light gray
		echo -e "\n\n\e[94mStep $currentStep - $1\e[0m\n"
	else
		# Underlined, light gray
		# Don't create newline
		echo -en "\n\n\e[94mStep $currentStep - $1\e[0m"
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

# Since the folders are made by root, lets change the group to the local user. We will change the owner
# later.
chgrp $userName db logs

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

	# Give group read and write access to every file
	chmod g+rw . -R
fi

# Making the rest of the script files executable for owner and group members
chmod g+x,u+x "$appLocation/load-dotenv.sh" "$scriptLocation/update.sh" "$scriptLocation/locales_apply_update.sh" "$scriptLocation/locales_update.sh"

echo -e "\t\e[32mDone!\e[0m\n"


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

	# Update permissions
	chown "radio-mnm:$userName" "$scriptLocation/radio-mnm.service"
	chmod g+rw "$scriptLocation/radio-mnm.service"

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

	echo -e "\t\t\t\t\t\t\e[32mDone!\e[0m\n"


	######################################
	#                                    #
	#     Enable automatic updating      #
	#                                    #
	######################################
	step "Enabling auto updating through cron" true
	if [ "$(crontab -l 2> /dev/null)" ]; then
		# A crontab file already exists. We are going to append our command to that file.
		crontab -l > tmp.cron
	else
		# No crontab file existed. We will build on an empty file:
		echo "" > tmp.cron
	fi

	# Remove earlier versions of our crontab:
	# Remove lines containing
	sed "/# Radio M&M: Don't edit this line by hand/d" tmp.cron > tmp.cron

	# Add the new crontab line
	# Note: This will be run as root
	echo "30	3	*	*	*	$scriptLocation/update.sh >> $appLocation/radio-mnm-update.log 2>&1  # Radio M&M: Don't edit this line by hand – it's autogenerated by a script." >> tmp.cron
	#     -		-	-	-	-
	#     |		|	|	|	|
	#     |		|	|	|	----- Day of week (0 - 7) (Sunday=0 or 7)
	#     |		|	|	------- Month (1 - 12)
	#     |		|	--------- Day of month (1 - 31)
	#     |		----------- Hour (0 - 23)
	#     ------------- Minute (0 - 59)

	# Add our modified tmp.cron as the new crontab for the root user
	crontab tmp.cron

	# Remove the temporary cron file
	rm tmp.cron
	echo -e "\t\t\t\t\e[32mDone!\e[0m\n"

	echo "







                           ,,    ,,                                                            
\`7MM\"\"\"Mq.               \`7MM    db               \`7MMM.     ,MMF' ,gM\"\"bg     \`7MMM.     ,MMF'
  MM   \`MM.                MM                       MMMb    dPMM   8MI  ,8       MMMb    dPMM  
  MM   ,M9   ,6\"Yb.   ,M\"\"bMM  \`7MM  ,pW\"Wq.        M YM   ,M MM    WMp,\"        M YM   ,M MM  
  MMmmdM9   8)   MM ,AP    MM    MM 6W'   \`Wb       M  Mb  M' MM   ,gPMN.  jM\"'  M  Mb  M' MM  
  MM  YM.    ,pm9MM 8MI    MM    MM 8M     M8       M  YM.P'  MM  ,M.  YMp.M'    M  YM.P'  MM  
  MM   \`Mb. 8M   MM \`Mb    MM    MM YA.   ,A9       M  \`YM'   MM  8Mp   ,MMp     M  \`YM'   MM  
.JMML. .JMM.\`Moo9^Yo.\`Wbmd\"MML..JMML.\`Ybmd9'      .JML. \`'  .JMML.\`YMbmm'\`\`MMm..JML. \`'  .JMML.
"
	echo -e "
                            --- $(date) ---

	    Radio M&M is now running as a service which starts automatically on boot.
You can control Radio M&M like any other service: \e[35msudo service radio-mnm start | stop | restart
"
fi