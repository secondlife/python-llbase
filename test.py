import sys

from distutils.core import Command
from distutils.util import get_platform
from glob import glob
from os import getcwd
from os.path import splitext, basename, join
from unittest import TextTestRunner
from unittest import TestLoader

class TestCommand(Command):
    user_options = [
        ('build-base=', 'b',
         "Base directory for build library."),
        ('build-purelib=', None,
         "Build directory for platform-neutral distributions."),
        ('build-platlib=', None,
         "Build directory for platform-specific distributions."),
        ('build-lib=', None,
         "Build directory for all distribution."),
        ('test-dir=', None,
         "Directory that contains the test definitions."),
        ]

    def initialize_options(self):
        self.build_base = join(getcwd(), 'build')
        self.build_purelib = None
        self.build_platlib = None
        self.build_lib = None
        self.test_dir = 'tests'

    def finalize_options(self):
        # We need distutil.util get_platform() to get arch
        self.plat = get_platform()
        #self.plat = "%s-%s" % (get_platform(), sys.version[:3])

        # Figure out where setup may have built things
        if self.build_purelib is None:
            self.build_purelib = join(self.build_base, 'lib')
        if self.build_platlib is None:
            self.build_platlib = join(self.build_base, 'lib.' + self.plat)

        # Finally, if no actual build_lib was set then assign to the
        # pure or platform lib as appropriate.
        if self.build_lib is None:
            if self.distribution.ext_modules:
                self.build_lib = self.build_platlib
            else:
                self.build_lib = self.build_purelib

    def run(self):
        # Invoke the 'build' command to meet the dependency
        self.run_command('build')
                        
        # remember old sys.path to restore it afterwards
        old_path = sys.path[:]

        # extend sys.path
        sys.path.insert(0, self.build_lib)
        #sys.path.insert(0, self.test_dir)

        testfiles = [ ]
        for t in glob(join(getcwd(), 'tests', '*.py')):
            if not t.endswith('__init__.py'):
                testfiles.append('/'.join(
                    ['tests', splitext(basename(t))[0]])
                )

        tests = TestLoader().loadTestsFromNames(testfiles)
        t = TextTestRunner(verbosity = 1)
        t.run(tests)

        # restore sys.path
        sys.path = old_path[:]
