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
appLocation="$(echo $scriptLocation | sed 's,/*[^/]\+/*$,,')"

# Load environment variables into this sub shell
source "$appLocation/load-dotenv.sh"

# Exit if auto updating is disabled
if [ "$(echo $mnm_autoUpdate)" = "False" ] || [ "$(echo $mnm_autoUpdate)" = "false" ] || [ "$(echo $mnm_autoUpdate)" = "0" ]; then
	echo "Auto updating is disabled via the environment variable: mnm_autoUpdate"
	exit
fi

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

echo -e "Started updating: $(date)"

#####################################
#                                   #
#             Update OS             #
#                                   #
#####################################
step "Update"
apt-get update -y

step "Upgrade"
apt-get upgrade -y

step "Clean up after updates"
apt-get autoremove -y
apt-get autoclean -y


#####################################
#                                   #
#            Update app             #
#                                   #
#####################################
step "Download Radio M&M updates"

# Temporary step to change the repository URL to Github (from GitLab)
git remote set-url origin https://github.com/etokheim/Radio-MnM.git
echo "The remote is now:"
git remote -v

# pip3 install --upgrade git+https://git.tokheimgrafisk.no/tokheim/radio-mnm/radio-mnm.git
git --git-dir="$appLocation/.git" pull

# TODO: Only install new dependencies if there was an update
step "Installing any new Python dependencies"
pip3 install -r "$appLocation/requirements.txt"

echo -e "Finished updating: $(date)"
service radio-mnm restart
