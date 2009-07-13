#!/usr/bin/make -f
# -*- makefile -*-

PYTHON=`which python`
VERSION=0.1.0
DESTDIR=/

all:
	@echo "make source - Create source package"
	@echo "make test - Run all tests"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

test:
	$(PYTHON) setup.py test

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

buildrpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

builddeb:
	fakeroot $(CURDIR)/debian/rules binary

clean:
	$(PYTHON) setup.py clean
	fakeroot $(CURDIR)/debian/rules clean
	rm -rf build/ dist/ MANIFEST
	find . -name '*.pyc' -delete

.PHONY: all, test, source, install, buildrpm, builddeb, clean
