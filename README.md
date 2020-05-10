# Radio M&M – An internet radio adapter

## Overview
Radio M&M (Radio mormor & morfar, or in English; Radio Grandma & Grandpa) is one of my COVID-19 projects. Because why not learn new stuff while in isolation? 🤓

#### Problem
The project sparked around christmas when my dad proposed to build a radio for my soon to be 99 years old grandpa which he could actually use. He struggles a bit with modern radios, but the main problem is bad/non-existant signal. You may think he must be living on the moon if he can't get a radio signal, but in Norway, the FM network is mostly turned off. It's been replaced by the more modern DAB+ standard, which is mostly a good thing. But the coverage is sometimes not the best.

This means that all of my grandpa's old radios are useless unless retrofitted. That's why we got him a DAB+ adapter. Which is just a small, speakerless radio which you connect to to the old radio's audio input. It works ok, but a lot of channels were registered without good enough signal to actually play. Therefor the adapter ended up not being used. Too advanced user interface, too many buttons, too many channels and few channels actually worked.

#### Solution
We figured we should be able to build something. Better, simpler and inherently more userfriendly. So we set out to retrofit his old Sølvsuper radio with a Raspberry Pi as a Internet radio adapter. His radio has now:
   - One extra button
      - Click to switch channel
   - A display to show the currently playing channel
   - Integration with the radio's power button. The adapter turns on/off with the radio.
   - A Raspberry Pi inside. With shared power chord etc.

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
   7. Run the configuration script:
      ```bash
      $ ./install.sh
      ```

### Development

   1. Follow the steps for a production setup until you are going to execute  setupEnvironment.sh. Don't execute it that way.
   2. Run the configuration script (notice the argument **--development**):
         ```bash
         $ ./install.sh --development
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
      2. `vlcpulse audio output error: PulseAudio server connection failure: Connection refused`
      3. `prefetch stream error: unimplemented query (264) in control`
         - No apparent impact

## Credits / contributers
Torstein Bjelland – Helped build the prototype.

Tore Tokheim – My dad. Initial idea and retrofitting the radio.

Erling Tokheim – Me. Idea, software and design.