#!/usr/bin/make -f
# -*- makefile -*-

PYTHON=`which python`
VERSION=0.2.0
DESTDIR=/
LIBPATH:=$(shell pwd)/build/lib.linux-x86_64-2.4
CLLSDPATH:=$(shell pwd)/build/lib.linux-x86_64-2.4/llbase
PYTHONPATH:=$(LIBPATH):$(CLLSDPATH)

all:
	@echo "make source - Create source package"
	@echo "make test - Run all tests"
	@echo "make doc - Generate the documentation"
	@echo "make install - Install on local system"
	@echo "make rpm - Generate a rpm package"
	@echo "make deb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

test:
	$(PYTHON) setup.py build
	PYTHONPATH=$(PYTHONPATH); nosetests

doc:
	make -C docs html

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

rpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

deb:
	fakeroot $(CURDIR)/debian/rules binary

clean:
	$(PYTHON) setup.py clean
	fakeroot $(CURDIR)/debian/rules clean
	rm -rf build/ dist/ MANIFEST
	find . -name '*.pyc' -delete
	make -C docs clean

.PHONY: all, source, test, doc, install, rpm, deb, clean
