#!/bin/bash
echo " _____         _   _             "
echo "|_   _|__  ___| |_(_)_ __   __ _ "
echo "  | |/ _ \/ __| __| | '_ \ / _' |"
echo "  | |  __/\__ \ |_| | | | | (_| |"
echo "  |_|\___||___/\__|_|_| |_|\__, |"
echo "                           |___/ "
echo
echo "Note: this will record NEW VCRs and overwrite old ones!"
echo

source bin/activate
VCR_RECORD_MODE=all coverage run --source pyfibot -m py.test
