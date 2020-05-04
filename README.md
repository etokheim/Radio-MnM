# Spec
Éin knapp
 - Klikk: Neste stasjon
 - Klikk og hold:
   - 2 sek: Standby-modus av/på
   - 7 sek: Skru heilt av pi
 - Korleis skru på att etter den er av?



# Setup
Install python dependencies:

 1. `sudo apt install vlc`
 2. `sudo apt install pulseaudio`
 3. `pulseaudio --start`
 4. Set the audio jack output as the primary output device:
    - `raspi-config` -> advanced -> audio -> output, force 3.5 mm audio jack
 5. `pip3 install -r requirements.txt`