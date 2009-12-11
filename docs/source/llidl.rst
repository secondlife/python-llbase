llidl
=====

LLIDL parser and value checker.

LLIDL is an interface description language for REST like protocols based on
the LLSD type system.

When comparing a particular llsd value to an llidl specification, there
are several possible outcomes:

* MATCHED the structure is as expected, the values all the right type
* CONVERTED the structure is as expected, but some values were of
  convertable values, structure may have gone through a system with
  more a restrictive type system
* DEFAULTED parts of the structure were missing, or set to undef
  these will be read as the default value, this may indicate that
  the structure comes from a system with an older definition
* ADDITIONAL parts of the structure do not correspond with the spec,
  they will be ignored
* MIXED some were defaulted , some were newer
* INCOMPATIBLE there were values that just didn't match and can't
  be converted        

.. autofunction:: llbase.llidl.parse_value

.. autofunction:: llbase.llidl.parse_suite

.. autoclass:: llbase.llidl.Suite
   :members:

.. autoclass:: llbase.llidl.Value
   :members:

.. autoexception:: llbase.llidl.MatchError

.. autoexception:: llbase.llidl.ParseError
