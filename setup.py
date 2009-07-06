#!/usr/bin/env python

import os.path
from distutils.core import setup, Extension

LLBASE_VERSION = '0.1.0'
LLBASE_SOURCE = 'src'
CLASSIFIERS = """\
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: MIT
Programming Language :: Python
Programming Language :: C
Topic :: Software Development
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Microsoft :: Windows
Operating System :: Unix
"""

sources = ["cllsd.c"]
sources = map(lambda x: os.path.join(LLBASE_SOURCE, x), sources)
cllsd_ext = Extension('llbase.cllsd', sources)


setup(
    name='llbase',
    version=LLBASE_VERSION,
    description='Base Linden Lab Pythoon modules',
    #author='',
    #author_email='',
    #url='http://bitbucket.org/phoenix_linden/llbase/',
    platforms=["any"],
    package_dir={'llbase':LLBASE_SOURCE},
    packages=['llbase'],
    license='MIT',
    classifiers=filter(None, CLASSIFIERS.split("\n")),
    requires=['eventlet', 'elementtree'],
    ext_modules=[cllsd_ext],
    )
