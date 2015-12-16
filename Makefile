#!/usr/bin/make -f
# -*- makefile -*-

#
# OPS-1487 - we're building this on Python 2.6, only, for now.
# 
#  This will need to be reverted post-wheezy.
#  
# PYTHON_VERSIONS := $(shell pyversions -vr)
PYTHON_VERSIONS := 2.6

INSTALL_TARGETS := $(addprefix install-version-,$(PYTHON_VERSIONS))
SOURCE_TARGETS := $(addprefix source-version-,$(PYTHON_VERSIONS))
BUILD_TARGETS := $(addprefix build-version-,$(PYTHON_VERSIONS))
TEST_TARGETS := $(addprefix test-version-,$(PYTHON_VERSIONS))
RPM_TARGETS := $(addprefix rpm-version-,$(PYTHON_VERSIONS))
VERSION=0.2.3
DESTDIR=/
NOSETESTS=`which nosetests`

all:
	@echo "make source - Create source package"
	@echo "make test - Run all tests"
	@echo "make doc - Generate the documentation"
	@echo "make install - Install on local system"
	@echo "make rpm - Generate a rpm package"
	@echo "make deb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

source: $(SOURCE_TARGETS)

$(SOURCE_TARGETS): source-version-%:
	python$* setup.py sdist $(COMPILE)

test: $(TEST_TARGETS)

$(TEST_TARGETS): test-version-%: build-version-%
	for entry in build/lib.*-$*/llbase; \
	do \
	  lib=$$(dirname $$entry); \
	  ver=$$(echo $$lib | sed 's/.*-//'); \
	  echo PYTHONPATH=$$entry:$$lib python$$ver $(NOSETESTS); \
	  PYTHONPATH=$$entry:$$lib python$$ver $(NOSETESTS) || rc=$$?; \
	done; \
	exit $$rc

build: $(BUILD_TARGETS)

$(BUILD_TARGETS): build-version-%:
	python$* setup.py build

doc:
	make -C docs html

install: $(INSTALL_TARGETS)

$(INSTALL_TARGETS): install-version-%: build-version-%
	python$* setup.py install --root $(DESTDIR) $(COMPILE) --no-compile

rpm: $(RPM_TARGETS)

$(RPM_TARGETS): rpm-version-%:
	python$* setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

deb:
	fakeroot $(CURDIR)/debian/rules binary

clean:
	$(PYTHON) setup.py clean
	fakeroot $(CURDIR)/debian/rules clean
	rm -rf build/ dist/ MANIFEST
	find . -name '*.pyc' -delete
	make -C docs clean

.PHONY: all source test doc install rpm deb clean\
   $(INSTALL_TARGETS)\
   $(SOURCE_TARGETS)\
   $(BUILD_TARGETS)\
   $(TEST_TARGETS)\
   $(RPM_TARGETS)
