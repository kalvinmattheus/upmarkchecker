UP Mark Checker
===============
__UP Mark Checker__ will check for new marks on the UP (University of Pretoria) Portal website for TUKS students and send an email notification when a new mark is available. The script has been casually tested on Ubuntu and Debian.


Installation and Usage
----------------------
Before you use the script, be sure to allow less secure apps at https://www.google.com/settings/security/lesssecureapps for your @tuks.co.za email account.

Download and extract the upmarkchecker-master.zip file and navigate inside the upmarkchecker-master folder, containing get.py or run the following commands:
```shell
sudo apt-get install git make
git clone https://github.com/kalvinmattheus/upmarkchecker
cd upmarkchecker
```

Run the following command to install the neccasary software for the script to run (see below for instructions without makefile):
```shell
make install
```

To start the script, run the following command in the same folder:
```shell
make run
```

Advanced Installation and Usage (without makefile)
--------------------------------------------------
Please follow the steps form the previous "Installation and Usage" section except for the make commands. Then open a terminal and run the following commands in order:
```shell
sudo apt-get install chromium-browser chromium-chromedriver || sudo apt-get install chromium chromium-driver    # install requirements
sudo apt-get install virtualenv python3 python3-pip    # install requirements
virtualenv -p python3 venv    # create a python virtual environment
source venv/bin/activate    # start the virtual environment
pip install -r requirements.txt    # install required software in the virtual environment
./get.py    # run the script
```
