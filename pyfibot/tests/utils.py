import re


def check_re(pattern, string):
    if not re.match(pattern, string, re.IGNORECASE | re.DOTALL):
        raise AssertionError('"%s" doesn\'t match "%s"' % (pattern, string))
