import os
from paver.easy import *
import paver.virtual
import paver.setuputils
from paver import svn
from paver.setuputils import setup, find_package_data, find_packages

options(
    #  bootstrap=Bunch(bootstrap_dir="bootstrap"),
      virtualenv=Bunch(
              packages_to_install=[],
              paver_command_line='develop',
              no_site_packages=True
          )
    )

install_requires = ['twisted', 'requests']

setup(
      name="PyFiBot",
      version="0.8",
      packages="pyfibot",
      description="The programmers' IRC bot",
      license="BSD",
      install_requires=install_requires
      )


@task
def prepare(options):
      pass

@task
def bootstrap(options):
    """create virtualenv in ./bootstrap"""
    try:
        import virtualenv
    except ImportError, e:
        raise RuntimeError("virtualenv is needed for bootstrap")

    options.virtualenv.no_site_packages = False
    options.bootstrap.no_site_packages = False
    #options.virtualenv.paver_command_line='prepare'
    call_task('paver.virtual.bootstrap')
