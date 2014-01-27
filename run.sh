#!/bin/sh
if [ ! -x databases/ ]; then
  mkdir databases
fi;

bin/python pyfibot/pyfibot.py config.yml
