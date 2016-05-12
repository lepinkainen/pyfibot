#!/bin/bash
echo " _____         _   _             "
echo "|_   _|__  ___| |_(_)_ __   __ _ "
echo "  | |/ _ \/ __| __| | '_ \ / _' |"
echo "  | |  __/\__ \ |_| | | | | (_| |"
echo "  |_|\___||___/\__|_|_| |_|\__, |"
echo "                           |___/ "
echo
echo "Note: this will only record new VCRs for missing tests"
echo "      old ones won't be overwritten. If a certain VCR"
echo "      is broken, remove it and run this script to regenerate"
echo

source bin/activate
VCR_RECORD_MODE=once coverage run --source pyfibot -m py.test
