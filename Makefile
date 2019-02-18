# line length and bare except
STYLE_IGNORE=E501,E722
# Ignore 'undefined name'
FLAKE_IGNORE=F821

test:
	pycodestyle --show-source --show-pep8 --ignore=$(STYLE_IGNORE) pyfibot/
	flake8 --ignore=$(STYLE_IGNORE),$(FLAKE_IGNORE) pyfibot/
