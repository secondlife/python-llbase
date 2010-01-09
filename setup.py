#!/usr/bin/env python

import os.path
import sys

from distutils.core import setup, Extension

import test


PACKAGE_NAME = 'llbase'
LLBASE_VERSION = '0.2.0'
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

setup(
    name=PACKAGE_NAME,
    version=LLBASE_VERSION,
    author='Phoenix Linden',
    author_email='enus@secondlife.com',
    url='http://bitbucket.org/lindenlab/llbase/',
    description='Base Linden Lab Python modules',
    platforms=["any"],
    package_dir={PACKAGE_NAME:LLBASE_SOURCE},
    packages=[PACKAGE_NAME, PACKAGE_NAME + ".test"],
    license='MIT',
    classifiers=filter(None, CLASSIFIERS.split("\n")),
    #requires=['eventlet', 'elementtree'],
    ext_modules=ext_modules,
    )
