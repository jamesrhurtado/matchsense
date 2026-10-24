PYTHON ?= .venv313/bin/python
.PHONY: dev test data data-check evaluate synthetic-list synthetic-data synthetic-evaluate web-build

dev:
	$(PYTHON) scripts/dev.py

test:
	$(PYTHON) -m pytest -q

data:
	$(PYTHON) -m simulator.generate

data-check:
	$(PYTHON) -m simulator.validate

evaluate:
	$(PYTHON) -m evals.run

synthetic-list:
	$(PYTHON) -m simulator.suite --list

synthetic-data:
	$(PYTHON) -m simulator.suite

synthetic-evaluate:
	$(PYTHON) -m evals.synthetic --check-baseline

web-build:
	npm --prefix apps/web run build

coverage-data:
	$(PYTHON) -m simulator.match_coverage
	$(PYTHON) -m simulator.matchday_demo
	$(PYTHON) -m simulator.flagship

coverage-evaluate:
	$(PYTHON) -m evals.match_coverage

coverage-dev:
	WHY_NOW_MATCH_COVERAGE=1 WHY_NOW_DB=.run/match-coverage.db $(PYTHON) scripts/dev.py
