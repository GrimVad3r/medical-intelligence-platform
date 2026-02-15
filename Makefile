.PHONY: install lint format test clean run-api run-dashboard run-dagster setup

install:
	pip install -U pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .

lint:
	flake8 src dashboards tests scripts --config .flake8
	mypy src --config-file mypy.ini || true

format:
	black src dashboards tests scripts --config black.toml
	isort src dashboards tests scripts --settings-path isort.cfg

test:
	pytest tests -v

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

clean:
	./scripts/cleanup.sh --all

run-api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-dashboard:
	streamlit run dashboards/streamlit_app.py

run-dagster:
	dagster dev -m src.orchestration.definitions

setup:
	./scripts/setup.sh
