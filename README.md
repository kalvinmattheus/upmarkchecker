UP Mark Checker
============
__UP Mark Checker__ will check for new marks on the UP Portal website and send an email notification when a new mark has been found.


Installation and Usage
-------------------------------------
Download and extract the upmarkchecker-master.zip file.  Inside the upmarkchecker-master folder, containing get.py, on Debian, open a terminal and run the following commands in order:
```shell
$	sudo apt-get install virtualenv python3 python3-pip chromium-browser chromium-chromedriver
$	virtualenv -p python3 venv
$	source venv/bin/activate
(venv)$	pip install -r requirements.txt
```

To start the script run the following command in the venv:
```shell
(venv)$	./get.py
```

