black := black --line-length 180
autoflake := autoflake --in-place --recursive --remove-unused-variables --expand-star-imports --remove-all-unused-imports

fmt:
	$(autoflake) .
	isort .
	$(black) .

check:
	PYTHONPATH=`pwd` tests/matchers.py
