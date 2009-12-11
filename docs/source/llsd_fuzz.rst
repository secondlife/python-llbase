Fuzz Testing LLSD
=================

The ``llsd_fuzz`` module is designed to make it easy to `fuzz test <http://en.wikipedia.org/wiki/Fuzz_testing>`_ LLSD-based tools and web services.  ``llsd_fuzz`` is a protocol-aware fuzz tester, which means that it generates data that is either syntactically correct or nearly so, which ensures that more of the protocol stack is covered by the tests than purely random data would.

A fuzz tester cannot test every possible error condition or flaw, but it is relatively easy to add, and always helps with automating negative testing.

Use it by calling one of the generator methods -- :meth:`LLSDFuzzer.structure_fuzz`, :meth:`LLSDFuzzer.xml_fuzz`, :meth:`LLSDFuzzer.binary_fuzz`, or :meth:`LLSDFuzzer.notation_fuzz` -- with a Python data structure that represents a legitimate input to the system under test.  The method will then yield an infinite sequence of variations.  Here's what that looks like::

    >>> from llbase.test import llsd_fuzz
    >>> from itertools import islice
    >>> lf = llsd_fuzz.LLSDFuzzer(10)
    >>> gen = lf.structure_fuzz({'a':'b'})
    >>> for i, f in enumerate(islice(gen, 3)):
    ...     print i, ":", repr(f)
    ... 
    0 : {'a': u'\ucf12\uf3eb\u25e6\ubedc\u5bef\uff1e\ue45e\u5c74\ue2ed\u74f2\u362c'}
    1 : {'a': '', u'\u75ba\u31e8\u8650\uf0e5\uc663\ue8da\u450f\u4d88\ueab4\u894d\ub7ce\u5dbb\u6d7e\uc5a5\u307e\ue5f0\u95f9\u3d7c': datetime.datetime(2000, 8, 31, 7, 5, 25)}
    2 : {}
    

The :meth:`LLSDFuzzer.structure_fuzz` method generates Python data structures that are serializable to LLSD.  The methods :meth:`LLSDFuzzer.xml_fuzz`, :meth:`LLSDFuzzer.binary_fuzz`, or :meth:`LLSDFuzzer.notation_fuzz` all generate strings using the respective LLSD serialization.

    
LLSDFuzzer objects are completely deterministic, so it is possible to reproduce failing test runs.  Here's how to set up your tests so that you can get the most out of them::

    sample_obj = {'key':'value'}
    fuzzer = llsd_fuzz.LLSDFuzzer()
	print "Seed is", repr(fuzzer.seed)
    for f in islice(fuzzer.xml_fuzz(obj), 1000):
        try:
            result = function_under_test(f)
            verify_result(result)
        except ExpectedError:
            pass  # expected, the function documents that it throws this exception
        except Exception, e:
            # unexexpected, we shouldn't have gotten here
            print "Fuzzed value that raised the exception was", f
            raise
                

.. automodule:: llbase.test.llsd_fuzz
	:members:
