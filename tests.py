from StringIO import StringIO
from textwrap import dedent
import unittest

class TestUserFuncs(unittest.TestCase):
    def test_user_exists(self):
        from fabfile import user_exists
        etc_passwd = StringIO(
            """test1:x:123:123:Test One:/home/test1:/bin/false
test2:x:456:456:Test Two:/home/test2:/bin/false""")
        self.assertTrue(user_exists("test1"))
        self.assertTrue(user_exists("test2"))
        self.assertFalse(user_exists("test3"))
        self.assertFalse(user_exists("false"))
        self.assertFalse(user_exists("home"))
        self.assertFalse(user_exists("Test1"))
        # Technically, user id is valid too, but we don't use it:
        # self.assertTrue(user_exists("123"))
        # self.assertTrue(user_exists(123))
        # self.assertFalse(user_exists("999"))
        # self.assertFalse(user_exists(999))
