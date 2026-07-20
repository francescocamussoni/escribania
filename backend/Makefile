.PHONY: install setup migrate seed demo-data user test run demo smoke frontend-install frontend-dev

export PYTHONPATH := src

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	/opt/homebrew/bin/python3.12 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

migrate:
	$(VENV)/bin/alembic upgrade head

seed:
	$(PYTHON) scripts/seed_config.py

demo-data:
	SEED_DEMO_DATA=true $(PYTHON) scripts/seed_demo_data.py

user:
	$(PYTHON) scripts/create_user.py --username admin --password tu-password --nombre-display "Admin"

test:
	$(VENV)/bin/pytest tests/ -v

demo:
	$(PYTHON) scripts/demo_calculo.py

run:
	$(VENV)/bin/uvicorn main:app --reload --port 8000

smoke:
	@chmod +x ../scripts/smoke_test.sh
	@../scripts/smoke_test.sh

frontend-install:
	cd ../frontend && npm install

frontend-dev:
	cd ../frontend && npm run dev

setup: migrate seed user
	@echo "Listo. Ejecutá 'make run' y probá http://localhost:8000/docs"
