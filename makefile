SHELL=/bin/bash

run:
	@echo "################################"
	@echo "    Starting UP Mark Checker    "
	@echo "################################"
	. venv/bin/activate; \
	python3 get.py

install:
	@echo "################################"
	@echo "   Installing UP Mark Checker   "
	@echo "################################"
	sudo apt-get install -y chromium-browser chromium-chromedriver || sudo apt-get install -y chromium chromium-driver
	sudo apt-get install -y  virtualenv python3 python3-pip
	rm -rf venv/
	virtualenv -p python3 venv
	. venv/bin/activate; \
	pip install -r requirements.txt; \
	deactivate
	@echo "################################"
	@echo "       Installation done        "
	@echo "################################"
