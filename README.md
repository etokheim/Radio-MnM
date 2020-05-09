# Radio M&M

## Setup
### Production

   1. Follow these steps to connect your display, power switch and button via the Pi's GPIO pins
   2. Open a terminal on your Raspberry Pi
   3. Navigate to where you want the app. Ie. in your home directory:
      ```bash
      cd
      ```
   4. Clone this repository (downloads the application files):
      ```bash
      git clone [url]
      ```
         - You can get the url by clicking the clone button in the top right corner. If in doubt, use the HTTPS version.
   5. Make a copy of `env.example` and rename it to `.env`
      ```bash
      $ cp env.example .env
      ```
   6. Edit the .env file with a text editor. Ie. Nano:
      ```bash
      $ nano .env
      ```
         - `ctrl` + `x` and follow the instructions to save and exit
   7. Make the configuration script executable:
      ```bash
      $ chmod +x scripts/setupEnvironment.sh
      ```
   8. Run the configuration script:
      ```bash
      $ ./scripts/setupEnvironment.sh
      ```

### Development

   1. Follow the steps for a production setup until you are going to execute  setupEnvironment.sh. Don't execute it that way.
   2. Run the configuration script (notice the argument **--development**):
         ```bash
         $ ./scripts/setupEnvironment.sh --development
         ```
   3. Load the environment variables into the shell you are using:
         ```bash
         $ source ./load-dotenv.sh
         ```
            - Note: you have to do this for every new shell you want to start the app from. Ie. if you restart your computer or open another terminal window, you have to repeat this step.
   4. Start the app:
      ```bash
      python3 -m radio_mnm
      ```
      - _Can be stopped by pressing `ctrl` + `c`_


## Debugging
Try the following if you don't get audio output:
 1. `pulseaudio --start`
 2. Set the audio jack output as the primary output device:
    - `raspi-config` -> advanced -> audio -> output, force 3.5 mm audio jack

## TODOs:

_Any help is appreciated!_

 1. Fix error messages:
    1. `ES_OUT_SET_(GROUP_)PCR is called too late (pts_delay increased to 1000 ms)`
        - Appears to have no negative side effects..? Though others says their video freezes if they are streaming video when the error comes.