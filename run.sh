#!/bin/bash
if [ ! -x databases/ ]; then
  mkdir databases
fi;

pipenv run pyfibot/pyfibot.py config.yml
