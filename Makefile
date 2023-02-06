PYTHON=python3.9
VENV=venv
BIN=$(VENV)/bin
REQUIREMENTS_FILE=requirements.txt

# Check if python is installed
.PHONY: check.python
check.python:
ifndef PYTHON
	$(error python3 is not installed or in PATH);
endif
	@exit 0;

## Setup
# Setup virtual environment
setup.venv: check.python
	@test -d $(VENV) || \
    ($(PYTHON) -m venv $(VENV););

# Setup dependencies from requirements.txt
setup.deps: setup.venv $(REQUIREMENTS_FILE)
	$(BIN)/pip install --upgrade pip && \
	$(BIN)/pip install -r $(REQUIREMENTS_FILE)

# Setup pre-commit hooks
.PHONY: setup.pre-commit
setup.pre-commit: setup.venv
	$(BIN)/pre-commit install && \
	$(BIN)/pre-commit install --hook-type commit-msg && \
	$(BIN)/pre-commit install --hook-type pre-push;

.PHONY: setup
setup: setup.deps setup.pre-commit
