PYTHON ?= .venv313/bin/python
.PHONY: dev test data data-check evaluate synthetic-list synthetic-data synthetic-evaluate web-build coverage-data coverage-evaluate coverage-dev live-dev episodes-data episodes-evaluate

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
	$(PYTHON) -m simulator.live_match

coverage-evaluate:
	$(PYTHON) -m evals.match_coverage

coverage-dev:
	WHY_NOW_MATCH_COVERAGE=1 WHY_NOW_DB=.run/match-coverage.db $(PYTHON) scripts/dev.py

# Build the web app once first; reuses the existing Azure model and local SQLite.
live-dev:
	$(PYTHON) scripts/live_dev.py

# Additive development scenes only; does not replace the current default demo.
episodes-data:
	$(PYTHON) -m simulator.episodes

episodes-evaluate:
	$(PYTHON) -m evals.episodes
