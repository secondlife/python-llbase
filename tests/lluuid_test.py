import unittest
import uuid

from llbase import lluuid

class LLUUIDTester(unittest.TestCase):
    """
    Aggreate all tests for lluuid
    """
    def testUUIDType(self):
        """
        Test whether the generated value is of type uuid.UUID

        Maps to test scenario module:lluuid:row#4
        """
        self.assertTrue(isinstance(lluuid.generate(), uuid.UUID))

    def testNotEqual(self):
        """
        Test whether two generated UUID is different.

        Maps to test scenario module:lluuid:row#5
        """
        one = lluuid.generate()
        two = lluuid.generate()
        self.assertNotEqual(one, two)

    def test_is_uuid(self):
        assert lluuid.is_str_uuid('771f6bee-41bf-43bf-989a-f66e8fefcabb')
        assert lluuid.is_str_uuid('00000000-0000-0000-0000-000000000000')
        assert lluuid.is_str_uuid('589EF487-197B-4822-911A-811BB011716A')
        assert lluuid.is_str_uuid('80df7610528c4d57940694a69e809044')
        assert lluuid.is_str_uuid('589EF487197B-4822-911A-811BB011716A')

    def test_is_not_uuid(self):
        assert not lluuid.is_str_uuid('0be1def8-0cd9-4735-bdb3')
        assert not lluuid.is_str_uuid(' 00000000-0000-0000-0000-000000000000')
        assert not lluuid.is_str_uuid('00000000-0000-0000-0000-000000000000 ')

if __name__ == '__main__':
    unittest.main()
