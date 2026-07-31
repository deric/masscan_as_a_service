.PHONY: all install lint fix test build clean

all: README.md

README.md: README.jinja2.md generate_readme.py src/masscan_as_a_service/__main__.py
	./generate_readme.py > README.md

install:
	python3 -m pip install -e '.[dev]'

lint:
	ruff check .

fix:
	ruff check --fix .

test:
	python3 -m pytest

build:
	python3 -m build

clean:
	rm -rf build dist src/*.egg-info .pytest_cache .ruff_cache
