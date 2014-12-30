#!/usr/bin/env python
import os
from setuptools import setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))
with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()
# print(requirements)

setup(
    name='pyfibot',
    version='0.9.4',
    description='Python IRC bot',
    long_description='An event-based IRC bot, based on twisted.words.protocols.irc',
    url='https://github.com/lepinkainen/pyfibot',
    author='Riku Lindblad',
    author_email='riku.lindblad@gmail.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Environment :: Console',
        'Framework :: Twisted',
        'Operating System :: OS Independent',
        'Topic :: Communications :: Chat :: Internet Relay Chat'
    ],
    license='MIT',
    packages=[
        'pyfibot',
        'pyfibot.modules',
        'pyfibot.util',
        'pyfibot.lib',
    ],
    package_data={
        '': [
            'static/example.yml',
            'static/example_full.yml',
            'static/config_schema.json',
            'static/GeoIP.dat',
        ]
    },
    zip_safe=False,
    install_requires=requirements,
    test_suite='nose.collector',
    entry_points={
        'console_scripts': ['pyfibot=pyfibot.pyfibot:main'],
    },
)
