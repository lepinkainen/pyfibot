#!/usr/bin/env python
import os
from paver.easy import *
import paver.virtual
import paver.setuputils
from paver import svn
from paver.setuputils import setup, find_package_data, find_packages

install_requires = ['twisted', 'requests', 'pyyaml', 'imdbpy', 'beautifulsoup', 'tvdb_api']

options(
      virtualenv=Bunch(
            packages_to_install=[],
            install_paver = True,
            paver_command_line=None,
            no_site_packages=True
          ),
      )


setup(
      name='pyfibot',
      version='0.9.2',
      description='Python IRC bot',
      long_description='An event-based IRC bot, based on twisted.words.protocols.irc',
      url='http://code.google.com/p/pyfibot/',
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
      packages=['pyfibot'],
      zip_safe=False,
      install_requires=install_requires,
      entry_points={
            'console_scripts' : ['pyfibot = pyfibot.pyfibot:main']
            }
      )

@task
@needs('generate_setup', 'minilib', 'setuptools.command.sdist')
def sdist():
      """Overrides sdist to make sure that our setup.py is generated."""
      pass

@task
def prepare(options):
      pass

@task
def bootstrap(options):
    """create virtualenv"""
    try:
        import virtualenv
    except ImportError, e:
        raise RuntimeError("virtualenv is needed for bootstrap")

    options.virtualenv.no_site_packages = False
    options.virtualenv.packages_to_install = install_requires
    options.bootstrap.no_site_packages = False
    options.virtualenv.paver_command_line='prepare'
    call_task('paver.virtual.bootstrap')
