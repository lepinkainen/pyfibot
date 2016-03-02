#!/bin/bash
if [ ! -x databases/ ]; then
  mkdir databases
fi;

source bin/activate
python pyfibot/pyfibot.py config.yml
