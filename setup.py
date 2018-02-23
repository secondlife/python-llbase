#!/usr/bin/env python

import os.path
import sys
import subprocess

from setuptools import setup, Command

# from http://stackoverflow.com/questions/2058802/how-can-i-get-the-version-defined-in-setup-py-setuptools-in-my-package :
# "make a version.py in your package with a __version__ line, then read it
# from setup.py using execfile('mypackage/version.py'), so that it sets
# __version__ in the setup.py namespace."

# [We actually define 'release', but same general idea.]

# "DO NOT import your package from your setup.py... it will seem to work for
# you (because you already have your package's dependencies installed), but it
# will wreak havoc upon new users of your package, as they will not be able to
# install your package without manually installing the dependencies first."

# However: in our case conf.py wants to read our debian/changelog file,
# relative to its __file__. But if we execfile("docs/source/conf.py"),
# os.path.dirname(__file__) is THIS directory! Trust that conf.py does not
# import any dependent modules, and just import it.
#execfile(os.path.join("docs", "source", "conf.py"))
docs_source = os.path.join(os.path.dirname(__file__), "docs", "source")
sys.path.insert(0, docs_source)
try:
    import conf
finally:
    sys.path.remove(docs_source)

PACKAGE_NAME = 'llbase'
LLBASE_VERSION = conf.release
LLBASE_SOURCE = 'llbase'
CLASSIFIERS = """\
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Topic :: Software Development
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Microsoft :: Windows
Operating System :: Unix
"""


class TestCommand(Command):
    user_options = []

    def run(self):
        """
        gather all of the tests modules in tests/ and run them
        """
        # shell out and run nosetests
        subprocess.call(['nosetests', '-sv'])

setup(
    name=PACKAGE_NAME,
    version=LLBASE_VERSION,
    author='Oz Linden',
    author_email='oz@lindenlab.com',
    url='http://bitbucket.org/lindenlab/llbase/',
    description='Base Linden Lab Python modules',
    long_description="""
===============
Linden Lab Base
===============

This project manages sources for some utility modules used by `Linden Lab <https://www.lindenlab.com>`_, the creators of `Second Life <https://www.secondlife.com>`_.

This source is available as open source; for details on licensing, see each file.

The canonical project repository is https://bitbucket.org/lindenlab/llbase
""",
    platforms=["any"],
    package_dir={PACKAGE_NAME:LLBASE_SOURCE},
    packages=[PACKAGE_NAME, PACKAGE_NAME + ".test"],
    license='MIT',
    classifiers=[_f for _f in CLASSIFIERS.split("\n") if _f],
    tests_require=['nose', 'mock'],
    install_requires=['requests'],
    cmdclass = {
                 'test': TestCommand,
               },
    )
