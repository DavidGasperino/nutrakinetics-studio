.PHONY: install test run

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"

test:
	. .venv/bin/activate && pytest -q

run:
	. .venv/bin/activate && streamlit run app/main.py
