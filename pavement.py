import os
from paver.easy import *

options(
    #  bootstrap=Bunch(bootstrap_dir="bootstrap"),
      virtualenv=Bunch(
              packages_to_install=[],
              no_site_packages=True
          )
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
    options.virtualenv.paver_command_line='prepare'
    call_task('paver.virtual.bootstrap')

