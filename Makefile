STYLE_IGNORE=E713,E501,W605,E722,E302,E402

test:
	pycodestyle --ignore=$(STYLE_IGNORE) pyfibot/
