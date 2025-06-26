# Pyfibot is back!

Thanks to the power of Claude Code, I was able to port the code to python3

- [uv](https://github.com/astral-sh/uv) is used to manage packages
- [Taskfiles](https://taskfile.dev/) instead of Makefiles

---

[![Python application](https://github.com/lepinkainen/pyfibot/actions/workflows/python-app.yml/badge.svg)](https://github.com/lepinkainen/pyfibot/actions/workflows/python-app.yml)

pyfibot
=======

A Python IRC-bot made using the [Twisted Matrix](http://twistedmatrix.com/trac/) IRC-library.

Supports online module reloading - only major core changes require a
restart. Extensive module & handler -support for easy extension and
customization.

Installation
------------

[Installation instructions](https://github.com/lepinkainen/pyfibot/wiki/Installation)

Module highlights
-----------------

* URL title fetching with custom handlers via API calls for speed and
efficiency
    * IMDb
    * Youtube / Dailymotion
    * Wikipedia
    * Imgur
    * Instagram
    * eBay
    * Spotify
* Bitcoin exchange rates
* Wolfram Alpha queries
* Weather
* RSS support

Features
--------

* Modular
    * Live refresh of modules and configuration
    * Coder friendly (a basic module requires just 2 lines of boilerplate
    code)
    * SSL-support
    * IPv6-support
    * virtualenv-support
    * Works with torify

Support can be found at #pyfibot on irc.nerv.fi and please contact
yllapito@nerv.fi if you want to connect outside of Finland (will be 
changed) or need help with IRC-network.


This product includes GeoLite data created by MaxMind, available from [http://www.maxmind.com](http://maxmind.com/).
