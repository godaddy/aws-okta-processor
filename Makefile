init:
	export PATH=$$(python3 -m site --user-base)/bin:$$PATH
	pip install poetry --force

	poetry update -vvv
	poetry install --remove-untracked -vvv
	poetry env info

format:
	poetry run black --skip-magic-trailing-comma --preview aws_okta_processor

lint:
	poetry run pylint aws_okta_processor
	poetry run flake8 aws_okta_processor
	poetry run mypy aws_okta_processor

test:
	export PYTHONPATH=".:aws_okta_processor/"
	poetry run py.test --cov-config .coveragerc --verbose --cov-report term --cov-report xml --cov=aws_okta_processor

build:
	poetry build

publish: build
	poetry config pypi-token.pypi $$PYPI_TOKEN && poetry publish
