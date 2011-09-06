#!/usr/bin/env python

import os.path
import sys
from glob import glob
import subprocess

from distutils.core import setup, Extension, Command
from distutils.spawn import spawn
from unittest import TextTestRunner, TestLoader

# from http://stackoverflow.com/questions/2058802/how-can-i-get-the-version-defined-in-setup-py-setuptools-in-my-package :
# "make a version.py in your package with a __version__ line, then read it
# from setup.py using execfile('mypackage/version.py'), so that it sets
# __version__ in the setup.py namespace."

# [We actually define 'release', but same general idea.]

# "DO NOT import your package from your setup.py... it will seem to work for
# you (because you already have your package's dependencies installed), but it
# will wreak havoc upon new users of your package, as they will not be able to
# install your package without manually installing the dependencies first."
execfile(os.path.join("docs", "source", "conf.py"))

PACKAGE_NAME = 'llbase'
LLBASE_VERSION = release                # from conf.py
LLBASE_SOURCE = 'llbase'
CLASSIFIERS = """\
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Programming Language :: Python
Programming Language :: C
Topic :: Software Development
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Microsoft :: Windows
Operating System :: Unix
"""
PLATFORM_IS_WINDOWS = sys.platform.lower().startswith('win')


sources = [os.path.join(LLBASE_SOURCE, "cllsd.c")]
ext_modules = [Extension(PACKAGE_NAME + '._cllsd', sources)]
if PLATFORM_IS_WINDOWS:
    ext_modules = None


class TestCommand(Command):
    user_options = []
    BUILD_DIR = 'build/lib.linux-x86_64-2.4'
    CLLSD_DIR = 'llbase'

    def initialize_options(self):
        cwd = os.getcwd()
        self._lib_path = os.path.join(cwd, self.BUILD_DIR)
        self._cllsd_path = os.path.join(cwd, self.BUILD_DIR, self.CLLSD_DIR)

    def finalize_options(self):
        pass

    def run(self):
        """
        gather all of the tests modules in tests/ and run them
        """

        # have to run build first
        self.run_command('build')

        # monkey with the python path
        python_path = self._lib_path + ':' + self._cllsd_path
        os.putenv('PYTHONPATH', python_path)

        # shell out and run nosetests
        subprocess.call(['nosetests', '-sv'])

setup(
    name=PACKAGE_NAME,
    version=LLBASE_VERSION,
    author='Huseby Linden',
    author_email='huseby@secondlife.com',
    url='http://bitbucket.org/lindenlab/llbase/',
    description='Base Linden Lab Python modules',
    platforms=["any"],
    package_dir={PACKAGE_NAME:LLBASE_SOURCE},
    packages=[PACKAGE_NAME, PACKAGE_NAME + ".test"],
    license='MIT',
    classifiers=filter(None, CLASSIFIERS.split("\n")),
    ext_modules=ext_modules,
    cmdclass = { 'test': TestCommand }
    )
