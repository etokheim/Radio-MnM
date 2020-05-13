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
#### What you'll need:
   1. An LCD display
   2. A power switch
      - If you are retrofitting we recommend connecting to the radio's own power switch
   3. A regular button
      - To switch channels
   4. A Raspberry Pi
      - Only works on PIs, but it shouldn't matter which version
      - On PI Zeros you also need a sound card for audio output

#### Setup the Pi
<details>
   <summary>Click to expand</summary>
   
   1. Download any version of Raspbian Buster
      - We recommend the Lite version
      - Should work with any Linux distribution, but this is not tested at all. If you do, you might have to edit the `install.sh` script, but otherwise it should run fine.
   2. Follow their [installation guide](https://www.raspberrypi.org/documentation/installation/installing-images/README.md), but **do not boot it** before reading the next step
   3. (Skip this if you are connecting to the Internet via a cable). If you don't want to connect an external display to setup WIFI, follow these steps to make the PI automatically connect to your local network after starting up:
      1. Open the `boot` partition on the newly formatted SD-card
      2. Create a new file named: `wpa_supplicant.conf`.
      3. Open this file in any editor and add the following:
         ```
         country=NO # Your 2-digit country code
         network={
            ssid="YOUR_NETWORK_NAME"
            psk="YOUR_PASSWORD"
         }
         ```
         - Note: for unsecured networks, replace `psk="YOUR_PASSWORD` with `key_mgmt=NONE`
   4. Enable ssh:
      1. Also in the `boot` partition on the Raspbian sd-card
      2. Create a new file named: `ssh`
         - Note that the file shouldn't have any file extension or content.
   5. Boot the PI and wait for it to start (about 2 minutes)
   6. Get the IP-address of the PI:
      - Option one:
         1. Open a terminal
            - Windows:
               1. Open CMD or PowerShell
            - Linux:
               1. `ctrl` + `alt` + `t`
         2. Type the following:
            ```sh
            ping raspberrypi.local
            ```
               - Press `ctrl` + `c` to stop pinging.
         3. If you get a reply, the output should contain your PI's IP. Copy it.
      - Option two:
         1. Open your router's administration page and look for the pi in it's device list.
            - Note that not all routers supports this
   7. Open a terminal
      - Windows:
         1. PowerShell, not CMD
      - Linux:
         1. `ctrl` + `alt` + `t`
   8. Type the following:
      ```sh
      ssh pi@[ip address]
      ```
      - Hit enter and type your password (probably `raspberry`)
   
You should now be connected to the Raspberry and can proceed to the next section on how to install the actual application!
</details>   

#### Install Radio M&M
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
   5. Go into the now downloaded application:
      ```bash
      $ cd radio-mnm
      ```
   6. Make a copy of `env.example` and rename it to `.env`
      ```bash
      $ cp env.example .env
      ```
   7. Edit the .env file with a text editor. Ie. Nano:
      ```bash
      $ nano .env
      ```
         - `ctrl` + `x` and follow the instructions to save and exit
   8. Run the configuration script:
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