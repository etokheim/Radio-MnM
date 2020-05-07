# Radio M&M

## Spec
Éin knapp
 - Klikk: Neste stasjon
 - Klikk og hold:
   - 2 sek: Standby-modus av/på
   - 7 sek: Skru heilt av pi
 - Korleis skru på att etter den er av?



## Setup
### Production

 1. `sudo apt install vlc`
 2. `sudo apt install pulseaudio`
 3. `pulseaudio --start`
 4. Set the audio jack output as the primary output device:
    - `raspi-config` -> advanced -> audio -> output, force 3.5 mm audio jack
 5. `pip3 install -r requirements.txt`

### Development

_Install everything from production including the following:_

 1. `sudo apt install gettext`

## Start

In the terminal you can start it in one of two ways:
 1. Start with logging output in the terminal:
    - _Can be stopped by pressing `ctrl` + `c`_
      ```sh
      python3 -m radio_mnm
      ```
 2. Start as a process
    - _Can only be stopped by killing the process_
        ```sh
        python3 -m radio_mnm &>> logAll.log &
        ```

## TODOs:

 1. Fix error messages:
    1. `ES_OUT_SET_(GROUP_)PCR is called too late (pts_delay increased to 1000 ms)`
        - Appears to have no negative side effects..? Though others says their video freezes if they are streaming video when the error comes.