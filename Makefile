.PHONY: all install lint format build clean

all: README.md

README.md: README.jinja2.md generate_readme.py src/masscan_as_a_service/__main__.py
	./generate_readme.py > README.md

install:
	python3 -m pip install -e '.[dev]'

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

build:
	python3 -m build

clean:
	rm -rf build dist src/*.egg-info
