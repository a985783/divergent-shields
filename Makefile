PYTHON ?= python3

.PHONY: install data process analysis-fast analysis-full verify clean-outputs

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

data:
	$(PYTHON) scripts/fetch_data.py
	$(PYTHON) scripts/fetch_data_upgrade.py
	$(PYTHON) scripts/fetch_oil.py

process:
	$(PYTHON) scripts/process_data.py

analysis-fast:
	$(PYTHON) run_all.py --fast

analysis-full:
	$(PYTHON) run_all.py

verify:
	$(PYTHON) scripts/verify_reproducibility.py

clean-outputs:
	rm -f paper/tables/*.csv
	rm -f paper/figures/*.png
