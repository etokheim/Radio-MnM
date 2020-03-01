# Spec
Éin knapp
 - Klikk: Neste stasjon
 - Klikk og hold:
   - 2 sek: Standby-modus av/på
   - 7 sek: Skru heilt av pi
 - Korleis skru på att etter den er av?



# Setup
Install python dependencies:

 1. `pip install rplcd`
 2. `pip install python-vlc`
 3. `sudo apt install vlc`
 4. `sudo apt install pulseaudio`
 5. `pulseaudio --start`
 6. Set the audio jack output as the primary output device:
    - `raspi-config` -> advanced -> audio -> output, force 3.5 mm audio jack
 7. `pip install zope.event`
    - Event system