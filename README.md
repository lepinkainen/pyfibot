# Project archived 7/2024

Porting this Python 2.x project to 3.x is way too much work for me.

I've replaced Pyfibot in my personal use with these three:

- IRC connector: https://github.com/lepinkainen/gobotlite
- Commands in AWS Lambda: https://github.com/lepinkainen/lambdabot
- Title parser in AWS Lambda: https://github.com/lepinkainen/titleparser

Both Lambda functions should be pretty easy to convert to run locally.

---

[![Python application](https://github.com/lepinkainen/pyfibot/actions/workflows/python-app.yml/badge.svg)](https://github.com/lepinkainen/pyfibot/actions/workflows/python-app.yml)
[![Updates](https://pyup.io/repos/github/lepinkainen/pyfibot/shield.svg)](https://pyup.io/repos/github/lepinkainen/pyfibot/)
[![Mergify Status][mergify-status]][mergify]

[mergify]: https://mergify.io
[mergify-status]: https://img.shields.io/endpoint.svg?url=https://gh.mergify.io/badges/lepinkainen/pyfibot&style=flat


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
