Fastest Elementtree
===================
Concealing some gnarly import logic in here. This module exports the
fastest elemettree interface available on your system.

The parsing exception raised by the underlying library depends on the
``ElementTree`` implementation we're using, so we provide an alias here.

Generally, you can use this module as a drop in replacement for how
you would use ``ElementTree`` or ``cElementTree``::


  from fastest_elementtree import fromstring
  fromstring(...)

Use ``ElementTreeError`` as the exception type for catching parsing
errors.
