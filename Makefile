.PHONY: test  dist

develop:
	pip3 install -e .[dev]

install:
	pip3 install .

uninstall:
	pip3 uninstall pianoputer

test:
	python3 setup.py pytest
