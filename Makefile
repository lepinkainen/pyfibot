# line length and bare except. Also ignore W503 and E203 as pycodestyle is breaking pep8
STYLE_IGNORE=E501,E722,W503,E203
# Ignore 'undefined name'
FLAKE_IGNORE=F821

test:
	pycodestyle --show-source --show-pep8 --ignore=$(STYLE_IGNORE) pyfibot/
	flake8 --ignore=$(STYLE_IGNORE),$(FLAKE_IGNORE) pyfibot/
	pylint --disable=all --enable=F,E,unreachable,duplicate-key,unnecessary-semicolon,global-variable-not-assigned,unused-variable,binary-op-exception,bad-format-string,anomalous-backslash-in-string,bad-open-mode pyfibot/
