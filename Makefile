STYLE_IGNORE=E713,E501,E722

test:
	pycodestyle --ignore=$(STYLE_IGNORE) pyfibot/
