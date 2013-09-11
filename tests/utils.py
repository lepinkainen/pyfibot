import re


def check_re(pattern, string):
    if re.match(pattern, string, re.IGNORECASE | re.DOTALL):
        return True
    return False
