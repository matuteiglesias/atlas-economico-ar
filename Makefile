PYTHON ?= python3

.PHONY: test-series capture-seed-series validate-series

test-series:
	$(PYTHON) -m unittest discover -s series/tests -p 'test_*.py'

capture-seed-series:
	$(PYTHON) series/capture.py

validate-series:
	$(PYTHON) series/validate.py
