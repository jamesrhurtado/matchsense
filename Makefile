PYTHON ?= .venv313/bin/python
.PHONY: dev test data data-check evaluate web-build

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

web-build:
	npm --prefix apps/web run build
