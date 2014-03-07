#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Small script to find variables that can be declared in config...
import os
import re
from pprint import pprint

get_rg = re.compile(r'[^\.](config|settings|network_conf)\.get\((.*?),(.*?)\)')


def clean_string(string):
    return string.strip().strip('\'"')


def find_gets(path):
    config_options = {}

    for f in os.listdir(path):
        if not f.endswith('.py'):
            continue

        with open(os.path.join(path, f), 'r') as f_handle:
            lines = f_handle.readlines()

        for l in lines:
            m = get_rg.search(l)
            if m:
                if f not in config_options:
                    config_options[f] = {}
                config_options[f][clean_string(m.group(2))] = clean_string(m.group(3))
    pprint(config_options)

if __name__ == '__main__':
    for p in ['pyfibot', 'pyfibot/modules', 'pyfibot/modules/available']:
        find_gets(os.path.join('.', p))
