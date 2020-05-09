# Loads all .env files into the current shell's environment.
# This is just for development, it's not used in any scripts.
if [ -f .env ]
then
  export $(cat .env | sed 's/#.*//g' | xargs)
fi
