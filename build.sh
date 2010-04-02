#!/bin/sh
#
# This file is used by Linden Lab's internal build process

set -x

# Check to see if we were invoked from the wrapper, if not, re-exec ourselves from there
if [ "x$arch" = x ]
then
  top=`hg root`
  if [ -x "$top/../buildscripts/hg/bin/build.sh" ]
  then
    exec "$top/../buildscripts/hg/bin/build.sh" "$top"
  elif [ -x "$top/../../parabuild/buildscripts/hg/bin/build.sh" ]
  then
    exec "$top/../../parabuild/buildscripts/hg/bin/build.sh" "$top"
  else
    cat <<EOF
This script, if called in a development environment, requires that the branch
independent build script repository be checked out next to this repository.
This repository is located at http://hg.lindenlab.com/parabuild/buildscripts
EOF
    exit 1
  fi
fi

# Check to see if we're skipping the platform
eval '$build_'"$arch" || pass

export DEB_BUILD_OPTIONS="revision=$revision"

if make test >"$build_log" 2>&1
then
  case "$arch" in
  Linux)
    rm -f ../python-llprogram*.deb
    rm -f debian/changelog.orig
    mv debian/changelog\
       debian/changelog.orig
    sed "s/^\\(llbase ([0-9]*\\.[0-9]*\\.\\)[0-9]*/\\1$revision/"\
       debian/changelog.orig\
     > debian/changelog
    make deb >>"$build_log" 2>&1
    hg revert debian/changelog
    pkg=`ls -1rt ../python-llbase*.deb | sed 1q`
    pkg_type=debian
    ;;
  Darwin) pass ;;
  CYGWIN)
    python setup.py bdist_wininst >"$build_log" 2>&1
    pkg=`ls -1rt dist/*.exe | sed 1q`
    pkg_type=installer
    ;;
  esac

  if [ "x$pkg" = x ]
  then
    succeeded=false
  else
    upload_item "$pkg_type" "$pkg" binary/octet-stream
    succeeded=true
  fi
else
  succeeded=false
fi

#eof
