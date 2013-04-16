Tweet-a-Watt
============
Original description of project by ladyada (Limor Fried of Adafruit): This project documents my adventures in learning how to wire up my home for wireless power monitoring. I live in a rented apartment so I don't have hacking-access to a meter or breaker panel. Since I'm still very interested in measuring my power usage on a long term basis, I built wireless outlet reporters. Building your own power monitor isn't too tough and can save money but I'm not a fan of sticking my fingers into 120V power. Instead, I'll used the existing Kill-a-watt power monitor, which works great and is available at my local hardware store.

RaspiWatt blog post:
====================
Tweet-a-Watt modified to run on Raspberry Pi
http://www.element14.com/community/groups/raspberry-pi/blog/2013/04/05/raspiwatt-discover-power-consumption-using-a-kill-a-watt-pi

References for RaspiWatt:
=========================
Send Raspberry Pi Data to COSM: Necessary Packages
http://learn.adafruit.com/send-raspberry-pi-data-to-cosm/necessary-packages

Adafruit 16x2 Character LCD + Keypad for Raspberry Pi: Usage
http://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/usage

Tweet-a-Watt software:
http://www.ladyada.net/make/tweetawatt/software.html

Install instructions for RaspiWatt:
==================================
<pre>
# Install system packages
cd ~/
mkdir dev
cd dev
sudo apt-get install git python-dev python-setuptools python-smbus i2c-tools python-pip

# Install RPi.GPIO module
sudo easy_install -U distribute
sudo pip install rpi.gpio

# Install EEML module (for Cosm)
wget -O geekman-python-eeml.tar.gz https://github.com/geekman/python-eeml/tarball/master
cd geekman-python-eeml*
sudo python setup.py install

# Active kernel modules for i2c (for LCD Pi Plate)
for Raspbian users, edit /etc/modules:
sudo nano /etc/modules

and add:
i2c-bcm2708 
i2c-dev

sudo i2cdetect -y 0 (if you are using a version 1 Raspberry Pi)
sudo i2cdetect -y 1 (if you are using a version 2 Raspberry Pi)      
This will search /dev/i2c-0 or /dev/i2c-1 for all address, and if an Adafruit LCD Plate is connected, it should show up at 0x20

# Install Adafruit library for LCD Pi Plate
git clone https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code.git
cd Adafruit-Raspberry-Pi-Python-Code
cd Adafruit_CharLCDPlate
sudo python Adafruit_CharLCDPlate.py
--------------
If you have a rev 2 (512MB) Pi, or if you're not getting anything displaying, it might be due to th I2C bus number change in the Pi hardware. Edit Adafruit_CharLCD.py using a command like "nano Adafruit_CharLCD.py" and change the line
lcd = Adafruit_CharLCDPlate(busnum = 0)
to
lcd = Adafruit_CharLCDPlate(busnum = 1)
--------------

# Install Tweet-a-Watt code modified for the RaspiWatt project
git clone https://github.com/misterbonnie/Tweet-a-Watt.git
cd Tweet-a-Watt
PYTHON_PATH=$HOME/dev/Adafruit-Raspberry-Pi-Python-Code/Adafruit_CharLCDPlate sudo python wattcher_cosm.py
</pre>
