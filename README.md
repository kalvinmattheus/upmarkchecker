UP Mark Checker
============
__UP Mark Checker__ will check for new marks on the UP Portal website and send an email notification when a new mark has been found.


Installation and Usage
-------------------------------------
Download and extract the upmarkchecker-master.zip file.  Inside the upmarkchecker-master folder, containing get.py, on Debian, open a terminal and run the following commands in order:
```shell
$	sudo apt-get install virtualenv python3 python3-pip chromium-browser chromium-chromedriver    # install requirements
$	virtualenv -p python3 venv    # create a python virtual environment
$	source venv/bin/activate    # start the virtual environment
(venv)$	pip install -r requirements.txt    # install required software in the virtual environment
```

Before you start the script for the first time, be sure to allow less secure apps at https://www.google.com/settings/security/lesssecureapps for your @tuks.co.za email account. 

Then create a file called "creds" (by default) in the pmarkchecker-master directory. The creds file should contain the following:
* Your UP username on the first line
* Your UP password on the second line
* True/False on the third indicating old password (do you have to click "proceed" after logging in on UP portal?)
* Preferred notification email address on the fourth line (optional, @tuks.co.za used by default)

For example:
```
u12345678
********
True
otheremail@example.com
```

To start the script run the following command in the venv:
```shell
(venv)$	./get.py
```
