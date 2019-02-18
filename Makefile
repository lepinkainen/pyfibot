STYLE_IGNORE=E501,E722

test:
	pycodestyle --show-source --show-pep8 --ignore=$(STYLE_IGNORE) pyfibot/
