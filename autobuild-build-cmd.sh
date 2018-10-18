#!/usr/bin/env bash

(cd ..; make test) || exit 1

# copy the license file to where autobuild wants it (required by autobuild)
test -d LICENSES || mkdir LICENSES
cp ../docs/llbase-license.txt LICENSES

#### TBD - find a way to run the self tests as part of all this

# create a source distribution of the llbase package
(cd ..; python setup.py sdist --format gztar)

# extract the version number from the distribution tarball name
dist_tarball=$(ls -t ../dist/llbase-*.tar.gz | head -n 1)
version=$(echo $dist_tarball | sed -E 's/.*llbase-//; s/\.tar.gz//;')
# create the version_file required by autobuild, adding the codeticket number
echo "$version.${AUTOBUILD_BUILD_ID:-0}" > VERSION.txt

# install the source package in a temporary virtual environment
TMP=$(mktemp -d virtual.XXXXXX)
trap "rm -rf ${TMP}* 2>/dev/null" EXIT
venv="${TMP}/environment"
virtualenv "${venv}"
. "${venv}/bin/activate"
pip install $dist_tarball

# find the path where the installed package files are in the virtual environment
installed_basedir=$(dirname $(python -c 'import llbase; print llbase.__file__;'))

# create the distribution tree we want for python as installed by autobuild
mkdir -p lib/python
# copy the installed files from the virtual environment to the autobuild conventional tree
cp -r "${installed_basedir}" lib/python
# clean out the self test files from the autobuild conventional tree
rm -rf lib/python/llbase/test
