PYTHON ?= python3
SOURCE_DATE_EPOCH ?= 1786828800

.PHONY: test-series test-figures test-publication test-growth test-real-economy growth-frontier capture-seed-series capture-bcra-series validate-series validate-figure-curation figure-qa-pack materialize-plots compile-publication sync-web build-atlas

test-series:
	$(PYTHON) -m unittest discover -s series/tests -p 'test_*.py'

test-figures:
	$(PYTHON) -m unittest discover -s figures/tests -p 'test_*.py'

test-publication:
	$(PYTHON) -m unittest discover -s publication/tests -p 'test_*.py'

test-growth:
	$(PYTHON) -m unittest discover -s growth/tests -p 'test_*.py'

test-real-economy:
	$(PYTHON) verticals/real_economy_vertical_v0_1/validation/validate.py

growth-frontier:
	$(PYTHON) scripts/build-growth-frontier.py

capture-seed-series:
	$(PYTHON) series/capture.py

capture-bcra-series:
	$(PYTHON) series/capture_bcra.py

validate-series:
	$(PYTHON) series/validate.py
	$(PYTHON) series/validate_bcra.py

validate-figure-curation:
	$(PYTHON) figures/curation.py validate

figure-qa-pack:
	$(PYTHON) figures/curation.py pack

materialize-plots:
	SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) $(PYTHON) figures/materialize.py
	$(PYTHON) figures/materialize_embed.py

compile-publication:
	$(PYTHON) scripts/build-publication.py --output site-data

sync-web:
	cd web && pnpm sync:data && pnpm sync:plots

build-atlas: test-real-economy validate-series materialize-plots compile-publication sync-web
	cd web && pnpm check
