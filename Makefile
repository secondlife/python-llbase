#!/usr/bin/make -f
# -*- makefile -*-

PYTHON=`which python`
VERSION=0.1.0
DESTDIR=/

all:
	@echo "make source - Create source package"
	@echo "make test - Run all tests"
	@echo "make docs - Generate the documentation"
	@echo "make install - Install on local system"
	@echo "make rpm - Generate a rpm package"
	@echo "make deb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

test:
	$(PYTHON) setup.py test

docs:
	doxygen doc/Doxyfile
	mv build/html  ./llbase-doc
	tar cvzf llbase-doc.tar.gz llbase-doc
	rm -rf llbase-doc
	mv llbase-doc.tar.gz build

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

.PHONY: all, source, test, docs, install, rpm, deb, clean
