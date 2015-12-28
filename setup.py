import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages
import os.path

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'README.md')) as f:
    long_description = f.read()

setup(
    name = "pyfibot",
    version = "0.9.5",
    description = "Python IRC bot based on twisted.words.irc",
#    long_description = long_description,
    url = "https://github.com/lepinkainen/pyfibot/",
    author = "Riku Lindblad",
    author_email = "riku.lindblad@gmail.com",
    license = "MIT",

    install_requires = ['twisted >= 12.0.0'],

    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Framework :: Twisted",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Communications :: Chat :: Internet Relay Chat",
        "Programming Language :: Python :: 2.7",
        ],
    keywords = "irc bot",

    packages=find_packages(),

    package_data = {
        'sample': ['example_full.yml']
        },

    entry_points = {
        'console_scripts': [
            'pyfibot=pyfibot.pyfibot:main',
            ],
        },

    setup_requires = ['pytest-runner'],
    tests_require = ['pytest'],
    )
