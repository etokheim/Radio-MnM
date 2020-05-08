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

#####################################
#                                   #
#        Install dependencies       #
#                                   #
#####################################
apt-get update -y

apt-get install -y \
	vlc \
	pulseaudio \
	python3 \
	python3-pip \
	nano \
	git

pip3 install -r "$scriptLocation/../requirements.txt"


#####################################
#                                   #
# Create missing files and folders  #
#                                   #
#####################################
echo -n "Creating necessary folders..."

# Make db and logs directories or the script will error out
if [ ! -d "$scriptLocation/../db" ]; then
	mkdir "$scriptLocation/../db"
fi

if [ ! -d "$scriptLocation/../logs" ]; then
	mkdir "$scriptLocation/../logs"
fi

echo "\tDone!"


#####################################
#                                   #
#         Register service          #
#                                   #
#####################################
echo -n "Registering service..."
cp "$scriptLocation/radio-mnm.service" "/etc/systemd/system"

# Reload daemon (necessary if a radio-mnm.service has already been registered).
sudo systemctl daemon-reload

# Start the service
sudo systemctl start radio-mnm.service

# Start the service on boot
sudo systemctl enable radio-mnm.service

echo "\t\tDone!"

echo "\nThe service is running successfully and starts automatically on boot"