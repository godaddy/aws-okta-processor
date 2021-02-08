PYTHONPATH=./src/:tests/

init:
	pip install --upgrade pipenv
	pip install wheel twine
	pipenv install --dev

test:
	PYTHONPATH=$(PYTHONPATH) pipenv run py.test --junitxml=report.xml

flake8:
	pipenv run flake8 src --max-line-length=120

coverage:
	PYTHONPATH=$(PYTHONPATH) pipenv run py.test --cov-config .coveragerc --verbose --cov-report term --cov-report xml --cov-report html --cov=aws_okta_processor tests

publish:
	python setup.py sdist bdist_wheel
	twine check dist/*
	twine upload dist/*
	rm -fr build dist .egg requests.egg-info
