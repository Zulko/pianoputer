.PHONY: test  dist

develop:
	pip3 install -e .[dev]

install:
	pip3 install .

uninstall:
	pip3 uninstall pianoputer

test:
	python3 setup.py pytest

dist:
	rm -rf dist
	python3 setup.py sdist bdist_wheel
	rm -rf build

testpypi:
	@read -p "Publish to testpypi? " -n 1 -r; \
	if [[ $$REPLY =~ ^[Nn] ]]; \
	then \
			echo "\nNot publishing"; exit 1; \
	fi
	python -m twine upload --repository testpypi dist/*

pypi:
	@read -p "Publish to pypi? " -n 1 -r; \
	if [[ $$REPLY =~ ^[Nn] ]]; \
	then \
			echo "\nNot publishing"; exit 1; \
	fi
	twine upload dist/*
