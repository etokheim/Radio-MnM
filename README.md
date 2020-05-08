# Radio M&M

## Setup
### Production

   1. Make a copy of `env.example` and rename it to `.env`
      ```bash
      $ cp env.example .env
      ```
   2. Edit the .env file
      ```bash
      $ nano .env
      ```
   3. Make the configuration script executable:
      ```bash
      $ chmod +x scripts/setupProductionEnvironment.sh
      ```
   4. Run the configuration script:
      ```bash
      $ ./scripts/setupProductionEnvironment.sh
      ```

### Development

_Install everything from production including the following:_

   1. Follow step 1 - 3 for production setup
   2. Run the configuration script (notice the argument **--development**):
         ```bash
         $ ./scripts/setupProductionEnvironment.sh --development
         ```
   3. Start the app:
      ```bash
      python3 -m radio_mnm
      ```
      - _Can be stopped by pressing `ctrl` + `c`_


## Debugging
Try the following if you don't get audio output:
 3. `pulseaudio --start`
 4. Set the audio jack output as the primary output device:
    - `raspi-config` -> advanced -> audio -> output, force 3.5 mm audio jack

## TODOs:

_Any help is appreciated!_

 1. Fix error messages:
    1. `ES_OUT_SET_(GROUP_)PCR is called too late (pts_delay increased to 1000 ms)`
        - Appears to have no negative side effects..? Though others says their video freezes if they are streaming video when the error comes.