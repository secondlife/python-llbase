#!/usr/bin/env bash

# create a binary distribution of the llbase package
(cd ..; python setup.py bdist --format gztar)

(cd ..; make test) || exit 1

# extract the binary distribution files we need into the autobuild structure
# the pathnames in the tarball will depend on whether or not there is a virtualenv
# active, so extract into a directory and then dig down to find the one we want
dist_tarball=../dist/llbase-*.tar.gz
# our cygwin install does not include the 'find' command, so grep for the directory and file we want
tar tzf ${dist_tarball} | grep -E '^.*/llbase[-/].*$' > target_files
# and then extract them, trimming the stuff we don't want from the pathnames
prefix_dir=$(dirname $(head -n 1 target_files))
test -d extract || mkdir extract
tar xzf ${dist_tarball} -C extract
mv "extract/${prefix_dir}/"* .

# Get the version number from the egg-info 
egg_info_file=$(ls -1 llbase-*.egg-info)
version=$(sed -En 's/^Version: ([0-9.]+).*/\1/p' "${egg_info_file}")
# create the version_file required by autobuild, adding the codeticket number
echo "$version.${revision:-0}" > VERSION.txt

# copy the license file to where autobuild wants it (required by autobuild)
test -d LICENSES || mkdir LICENSES
cp ../docs/llbase-license.txt LICENSES
