# Run `make` on its own to see what is available.
#
# Everything runs through pipenv so the locked versions are what execute.
# Override to use an interpreter you have already set up:
#     make test PYTHON=python3

PYTHON ?= pipenv run python

.DEFAULT_GOAL := help
.PHONY: help install test refresh

help:
	@echo "install   install the locked dependencies into a pipenv environment"
	@echo "test      run the unit tests (no network needed)"
	@echo "refresh   re-download from the portal and rewrite both reports and the CSV"

install:
	pipenv install --dev

test:
	$(PYTHON) -m unittest discover -s tests -t .

# There is no cache, so this always pulls current data from the portal.
# Takes about 12 seconds and needs network access.
refresh:
	$(PYTHON) main.py
