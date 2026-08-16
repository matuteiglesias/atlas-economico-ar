PYTHON ?= python3
SOURCE_DATE_EPOCH ?= 1786828800

.PHONY: test-series capture-seed-series capture-bcra-series validate-series materialize-plots compile-publication sync-web build-atlas

test-series:
	$(PYTHON) -m unittest discover -s series/tests -p 'test_*.py'

capture-seed-series:
	$(PYTHON) series/capture.py

capture-bcra-series:
	$(PYTHON) series/capture_bcra.py

validate-series:
	$(PYTHON) series/validate.py
	$(PYTHON) series/validate_bcra.py

materialize-plots:
	SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) $(PYTHON) figures/materialize.py

compile-publication:
	$(PYTHON) scripts/build-publication.py --output site-data

sync-web:
	cd web && pnpm sync:data && pnpm sync:plots

build-atlas: validate-series materialize-plots compile-publication sync-web
	cd web && pnpm check
